class LogRepository:
    def __init__(self, db):
        self.db = db

    def insert_log(self, level: str, message: str, data: str):
        self.db.execute(
            "INSERT INTO logs(level, message, data, created_at) VALUES(?,?,?,CURRENT_TIMESTAMP)",
            (level, message, data),
        )
