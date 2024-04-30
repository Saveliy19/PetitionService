from app.db import DataBase

from app.config import host, port, user, database, password

db = DataBase(host, port, user, database, password)

