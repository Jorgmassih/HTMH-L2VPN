import jwt
from datetime import datetime, timedelta


class WebToken:

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.encrypt_algorithm = 'HS256'

    def create_token(self, username: str):
        try:
            today = datetime.now()
            expiration_time = today + timedelta(hours=24)
            payload = {
                'iar': today.timestamp(),
                'exp': expiration_time.timestamp(),
                'sub': username
            }

            token = jwt.encode(
                payload=payload,
                key=self.secret_key,
                algorithm=self.encrypt_algorithm,
            )

            return {'expires': expiration_time, 'token': token}

        except Exception as e:
            print(e)
            return None

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, 'utf-8')
            return payload

        except jwt.DecodeError as e:
            print(e)
            return None
        except jwt.InvalidTokenError as e:
            print(e)
            return None

    def validate_token(self, token):
        try:
            jwt.decode(token, self.secret_key, 'utf-8')
            return True

        except jwt.exceptions.ExpiredSignatureError as e:
            print(e)
            return False

        except jwt.exceptions.InvalidSignatureError as e:
            print(e)
            return False

        except jwt.exceptions.InvalidTokenError as e:
            print(e)
            return None

