import jwt
import secrets
import datetime

#secret_key = secrets.token_hex(16)

def create_jwt(username, id, secret_key):
    payload = {}
    payload["id"] = id
    payload["username"] = username
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)

    token = jwt.encode(payload=payload, key=secret_key)

    print(payload, secret_key)
    print(token)
    return token


def decode_jwt(returned_token, secret_key, algorithm):
    data = jwt.decode(returned_token, secret_key, algorithms=algorithm)
    print(data)
    return data
        

if __name__ == "__main__":
    token = create_jwt(username="john doe", id=3, secret_key="meranaamchinchinchu")
    print(token)
    print(decode_jwt(returned_token=token, secret_key="meranaamchinchinchu"))