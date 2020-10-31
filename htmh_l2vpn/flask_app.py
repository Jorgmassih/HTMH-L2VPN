from flask import Flask, request, Response
import secrets
from htmh_l2vpn.web_services_stuff.jwt import WebToken
import json

app = Flask(__name__)

secret_key = secrets.token_hex(25)
jwt = WebToken(secret_key=secret_key)


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    print(data)
    username, password = data['username'], data['password']
    db_validation = True

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


if __name__ == '__main__':
    app.run(debug=True)
