from flask import Flask, request, abort, make_response, jsonify
import os
import psycopg2 as psy
from jwts import create_jwt, decode_jwt
from functools import wraps
import jwt
import secrets


user = os.getenv("postgres_username")
host = os.getenv("postgres_host")
password = os.getenv("postgres_password")


class DatabaseConnection:
    def __init__(self, user=user, host=host, password=password, port=5432, database="people"):
        self.user = user
        self.host = host
        self.password = password
        self.port = port
        self.database= database

    def connect(self):
        connection = psy.connect(host=self.host,
                                  user=self.user, 
                                  password=self.password, 
                                  port=self.port, 
                                  database=self.database)
        
        return connection


app = Flask(__name__)

app.config["secret_key"] = secrets.token_hex(16)
app.config["decoding_algorithm"] = ["HS256", ]

#Middleware - Only Valid IPS can access the routes
accepted_ips = ["192.168.64.3", "127.0.0.1"]
@app.before_request
def restrict_ips():
    client_ip = request.remote_addr
    print(client_ip)

    if client_ip not in accepted_ips:
        abort(403) #Not Authorized


#Decorator to check if the user is the same that logged in
def login_required(f):
    @wraps(f)

    def decorated(*args, **kwargs):
        token = request.headers['token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        
        try: 
            data = decode_jwt(returned_token=token, secret_key=app.config['secret_key'], algorithm=app.config['algorithm'])
            print(data)
        
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 403
        
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 403
        
        except Exception as e:
            return jsonify({'message': f"Token Error: {str(e)}"})
        
        return f(*args, **kwargs)
    
    return decorated



@app.route("/login", methods=['POST'])
def login():
    username = request.authorization['username']
    username = username.title()
    password = request.authorization['password']
    
    conn = DatabaseConnection().connect()
    cursor = conn.cursor()
    cursor.execute("""SELECT password, id from user_pw
                   WHERE username = %s""", (username, ))
    
    pw = cursor.fetchall()

    if pw[0][0] == password:
        token = create_jwt(username=username, id=pw[0][1], secret_key=app.config['secret_key'])

        return jsonify({'token': token})

    return make_response('Could Not Verify!', 403, {'WWW-Authenticate': 'Basic realm = "Login Required"'})


@app.route("/get_all")
@login_required
def all_data():
    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM people_properties;")
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(data)


@app.route("/Insert_New_Entry", methods=['POST'])
@login_required
def insert_new():
    new_entry = request.json
    print(new_entry)
    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
    cursor.execute("""INSERT INTO people_properties(id, name, age, country, gender) 
                            VALUES (%s, %s, %s, %s, %s)""", 
                                (new_entry.get('id'),
                                new_entry.get('name'),
                                new_entry.get('age'), 
                                new_entry.get('country'), 
                                new_entry.get('gender')))
                    
    connection.commit()

    cursor.close()
    connection.close()

    return "Insert Successful"


@app.route("/delete_entry", methods=['POST'])
@login_required
def delete_entry():
    delete = request.headers['id']
    print(delete)
    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
    cursor.execute("""DELETE FROM people_properties
                        WHERE id = %s""", delete)
                    
    connection.commit()

    cursor.close()
    connection.close()

    return "Delete Successful"
    
   
@app.route("/UPDATE", methods=['POST'])
@login_required
def update():    
    update_query = request.json
    print(update_query)

    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
                    
    if update_query.get('update_what') == 'age':
        cursor.execute("""UPDATE people_properties
                            SET age = %s
                            WHERE id = %s""", (update_query.get('update_id'), update_query.get('update_to')))
                        
    elif update_query.get('update_what') == 'name':
        cursor.execute("""UPDATE people_properties
                            SET name = %s 
                            WHERE id = %s""", (update_query.get('update_to'), update_query.get('update_id')))
                        
    elif update_query.get('update_what') == 'country':
        cursor.execute("""UPDATE people_properties
                            SET country = %s 
                            WHERE id = %s""", (update_query.get('update_id'), update_query.get('update_to')))
                        
    else:
        cursor.execute("""UPDATE people_properties
                            SET gender = %s
                            WHERE id = %s""", (update_query.get('update_id'), update_query.get('update_to')))


        connection.commit()

        cursor.close()
        connection.close()


        return "Update Complete"


if __name__ == "__main__":
    app.run(debug=True)


