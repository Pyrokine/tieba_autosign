import pymysql
import Privacy


def ExecuteSQL(sql):
    db = pymysql.connect(host="localhost", user=Privacy.SQLUsername, password=Privacy.SQLPassword, database="tieba", charset="gbk")
    cursor = db.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    return result

