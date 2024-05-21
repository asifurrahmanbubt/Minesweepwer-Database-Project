import mysql.connector
from mysql.connector import Error

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='minesweeper_db'
        )
        if connection.is_connected():
            db_info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_info)
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as e:
        print(f"Error: {e}")
        connection.rollback()

def fetch_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Error: {e}")
        return None

def register_user(connection, username, password, email):
    query = f"INSERT INTO users (username, password, email) VALUES ('{username}', '{password}', '{email}')"
    execute_query(connection, query)

def save_game_state(connection, user_id, game_state, difficulty, score):
    query = f"INSERT INTO games (user_id, game_state, difficulty_level, score) VALUES ({user_id}, '{game_state}', '{difficulty}', {score})"
    execute_query(connection, query)

def load_game_settings(connection, user_id):
    query = f"SELECT game_id, game_state, difficulty_level, score FROM games WHERE user_id = {user_id} ORDER BY game_id DESC"
    result = fetch_query(connection, query)
    return result

def get_user_id(connection, username):
    query = f"SELECT user_id FROM users WHERE username = '{username}'"
    result = fetch_query(connection, query)
    if result:
        return result[0][0]
    return None

def validate_user(connection, username, password):
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    result = fetch_query(connection, query)
    if result:
        return True
    return False

def fetch_user_statistics(connection, user_id):
    query = f"SELECT game_state, difficulty_level, score FROM games WHERE user_id = {user_id}"
    result = fetch_query(connection, query)
    return result
