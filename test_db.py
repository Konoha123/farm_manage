import mysql.connector


def list_databases(host, user, password):
    try:
        # 连接到MySQL服务器
        connection = mysql.connector.connect(host=host, user=user, password=password)

        cursor = connection.cursor()

        # 执行SQL命令以显示所有的数据库
        cursor.execute("SHOW DATABASES")

        print("Databases on {}: ".format(host))
        for db in cursor:
            print(db[0])

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print("Error:", err)


def list_tables(host, user, password):
    try:
        # 连接到MySQL服务器
        connection = mysql.connector.connect(host=host, user=user, password=password)

        cursor = connection.cursor()

        # 执行SQL命令以显示所有的数据库
        cursor.execute("USE mysql")
        cursor.execute("SHOW TABLES")

        print("Tables on {}: ".format(host))
        for db in cursor:
            print(db[0])

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print("Error:", err)


if __name__ == "__main__":
    HOST = "10.5.10.97"
    USER = "dashuai"
    PASSWORD = " "  # 密码是一个空格
    list_databases(HOST, USER, PASSWORD)
    list_tables(HOST, USER, PASSWORD)
