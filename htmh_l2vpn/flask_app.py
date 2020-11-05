from functools import wraps

from flask import Flask, request, Response

from htmh_l2vpn.mongodb.mongo_driver import User
from htmh_l2vpn.web_services_stuff.jwt_handler import WebToken
import json

app = Flask(__name__)

secret_key = "secret"
jwt = WebToken(secret_key=secret_key)

allowed_cross_domains = ['http://127.0.0.1:3000']


def auth_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        access_token = request.cookies.get('_access_token_')
        if not access_token:
            return Response(json.dumps({'message': 'No access token'}), 401)

        else:
            validation = jwt.validate_token(access_token)
            if validation is None:
                return Response(json.dumps({'message': 'An error has occurred with the server at middleware'}), 500)

            return f(*args, **kwargs) if validation else Response(json.dumps({'message': 'No authorization'}), 401)

    return wrap


@app.after_request
def apply_caching(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "content-type"
    response.headers['Access-Control-Allow-Methods'] = "GET,PUT,POST,DELETE"

    request_domain = request.headers.get('Origin')
    if request_domain in allowed_cross_domains:
        response.headers["Access-Control-Allow-Origin"] = request_domain

    print(request_domain)

    return response


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
    username, password = data['username'], data['password']
    db_validation = User(user_id=username).login(password=password)

    if db_validation:
        token = jwt.create_token(username)
        token_str = token['token'].decode()
        #record_log(session_id=token_str, log_type='Login')

        if token is None:
            return Response({'message': 'Error while creating token'}, 500)

        resp = Response(json.dumps({'message': 'User authenticated'}), 201)
        resp.set_cookie(key="_access_token_", value=token_str, httponly=True, expires=token['expires'])
        return resp

    return Response(json.dumps({'message': 'User not found'}), 401)


@app.route('/api/v1/auth/logout', methods=['GET'])
def logout():
    token = request.cookies.get('_access_token_')
    print(type(token))
    print(token)
    username = jwt.decode_token(token)['sub']
    User(user_id=username).logout()
    resp = Response(json.dumps({'message': 'removing cookie token'}), 200)
    resp.set_cookie(key="_access_token_", expires=0)
    return resp


@app.route('/api/v1/auth/is-auth', methods=['GET'])
@auth_required
def is_auth():
    token = request.cookies.get('_access_token_')
    validation = jwt.validate_token(token)
    if validation:
        return Response(json.dumps({'message': 'Authorized'}), status=200)

    else:
        return Response(json.dumps({'message': 'Unauthorized'}), status=403)


@app.route('/api/v1/device/list', methods=['GET'])
@auth_required
def device_list():
    token = request.cookies.get('_access_token_')
    user = jwt.decode_token(token)['sub']
    d_list = User(user_id=user).get_hosts()

    return Response(json.dumps({'data': d_list}), status=200)


if __name__ == '__main__':
    app.run(debug=True)
