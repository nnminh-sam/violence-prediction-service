from enum import Enum
from decouple import config


class EnvironmentConfig(Enum):
    DEBUG = config("DEBUG", default=False, cast=bool)
    SECRET_KEY = config('SECRET_KEY')
    DB_HOST = config('DB_HOST')
    DB_PORT = config('DB_PORT')
    DB_NAME = config('DB_NAME')
    DB_USER = config('DB_USER')
    DB_PASSWORD = config('DB_PASSWORD')