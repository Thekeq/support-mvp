import sqlite3


class DataBase:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        # Создание таблицы, если она еще не существует
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    user_admin TEXT
                )
            ''')
        self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users_banned (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER
                )
            ''')

        self.connection.commit()

    def user_admin(self, user_id):
        with self.connection:
            result = self.cursor.execute("SELECT user_admin FROM `users` WHERE `user_id` = ?", (user_id,)).fetchall()
            return result

    def get_admins(self):
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM `users` WHERE `user_admin` = 1", ()).fetchall()
            return [row[0] for row in result]

    def users_banned(self):
        with self.connection:
            result = self.cursor.execute("SELECT user_id FROM `users_banned`", ()).fetchall()
            return [row[0] for row in result]

    def ban(self, user_id):
        with self.connection:
            if user_id not in self.users_banned():
                self.cursor.execute(
                    "INSERT INTO users_banned (`user_id`) VALUES (?)",
                    (user_id,)
                )

    def add_user(self, user_id):
        with self.connection:
            self.cursor.execute(
                "INSERT INTO users (`user_id`, `user_admin`) VALUES (?, ?)",
                (user_id, True)
            )
