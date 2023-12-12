from flask import Flask, request, abort
import psycopg2 as psy
import os
import json 

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


accepted_ips = ["192.168.64.3", "127.0.0.1"]
@app.before_request
def restrict_ips():
    client_ip = request.remote_addr
    print(client_ip)

    if client_ip not in accepted_ips:
        abort(403) #Not Authorized


def logged_in():
    username = request.authorization['username']
    username = username.title()
    password = request.authorization['password']
    print(username)
    print(password)

    conn = DatabaseConnection().connect()
    cursor = conn.cursor()
    cursor.execute("""SELECT * FROM user_pw WHERE username = %s""", (username,))
            
    info = cursor.fetchall()
    print(info)
            
    return  username == info[0][1] and password == info[0][2]
        

def check(route_function):
    def wrapper(*args, **kwargs):
        if logged_in(): 
            return route_function(*args, **kwargs)
        else:
            abort(401)
    
    wrapper.__name__ = route_function.__name__
    return wrapper


@app.route("/SignIn", methods=['POST'])
def signin():
    username = request.authorization['username']
    password = request.authorization['password']

    print(username, password)

    conn = DatabaseConnection().connect()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO user_pw(username, password)
                   VALUES
                   (%s, %s);""", (username, password))
    
    conn.commit()
    
    cursor.close()
    conn.close()

    return "Signin Successful!"


@app.route("/Login", methods=['POST'])
def login():
    if logged_in():
        return "Login Successful"
    else:
        abort(401)


@app.route("/")
@check
def all_data():
    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM people_properties;")
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return json.dumps(data)


@app.route("/Insert_New_Entry", methods=['POST'])
@check
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


@app.route("/delete_entry")
@check
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
    

@app.route("/UPDATE", methods=['GET', 'POST'])
@check
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
    app.run(debug=True, port=5000)

