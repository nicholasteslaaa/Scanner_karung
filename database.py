import sqlite3
from dotenv import  load_dotenv
import  os

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")


def get_db():
    conn = sqlite3.connect(DB_URL)
    cursor = conn.cursor()
    return conn,cursor

def insert_data1(c1,c2,totallapis,rows,current_time):
    conn,cursor = get_db()

    # SQL query with placeholders
    sql_insert_query = """INSERT INTO infocam1 (timestamp, lapis1, lapis2, totallapis,rows) VALUES (  ?, ?, ?, ?, ?)"""
    data = (current_time, c1, c2,totallapis,rows)
    cursor.execute(sql_insert_query, data)
    conn.commit()

    cursor.close()
    conn.close()

def insert_data2(c1,c2,totallapis,rows,current_time):
    conn,cursor = get_db()

    # SQL query with placeholders
    sql_insert_query = """INSERT INTO infocam2 (timestamp, lapis1, lapis2, totallapis,rows) VALUES (?,?, ?, ?, ?)"""
    data = (current_time, c1, c2,totallapis,rows)
    cursor.execute(sql_insert_query, data)
    conn.commit()

    cursor.close()
    conn.close()
def insert_data3(variasi,jumlah,current_time):
    conn,cursor =  get_db()

    # SQL query with placeholders
    sql_insert_query = """INSERT INTO inventory_data (timestamp, variasi, jumlah) VALUES (?,?,?)"""
    data = (current_time,variasi,jumlah)
    cursor.execute(sql_insert_query, data)
    conn.commit()

    cursor.close()
    conn.close()
