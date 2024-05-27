import pymysql.cursors
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'admin123',
    'db': 'food_recommendation_db',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}