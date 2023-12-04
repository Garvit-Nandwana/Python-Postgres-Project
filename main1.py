from flask import Flask, request, abort 
import psycopg2 as psy
import os 

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


accepted_ips = ["<IP1>", "<IP2>"]
@app.before_request
def restrict_ips():
    client_ip = request.remote_addr

    if client_ip not in accepted_ips:
        abort(403) #Not Authorized
    

@app.route("/")
def all_data():
    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM people_properties;")
    data = cursor.fetchall()

    cursor.close()
    connection.close()

    return data


@app.route("/Insert_New_Entry", methods=['GET', 'POST'])
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
def update():
    update_query = request.json
    print(update_query)

    connection = DatabaseConnection().connect()
    cursor = connection.cursor()
    
    if update_query.get('update_what') == 'age':
         cursor.execute("""UPDATE people_properties
                        SET age = %s
                        WHERE id = %s""",
                          (update_query.get('update_id'), update_query.get('update_to')))
        
    elif update_query.get('update_what') == 'name':
        cursor.execute("""UPDATE people_properties
                       SET name = %s 
                       WHERE id = %s""",
                          (update_query.get('update_to'), update_query.get('update_id')))
        
    elif update_query.get('update_what') == 'country':
        cursor.execute("""UPDATE people_properties
                       SET country = %s 
                       WHERE id = %s""",
                          (update_query.get('update_id'), update_query.get('update_to')))
        
    else:
        cursor.execute("""UPDATE people_properties
                        SET gender = %s
                        WHERE id = %s""",
                          (update_query.get('update_id'), update_query.get('update_to')))


    connection.commit()

    cursor.close()
    connection.close()


    return "Update Complete"


if __name__ == "__main__":
    app.run(debug=True)
