import json

from starlette.config import Config

config = Config(env_file=".env")

FIREBASE_CERTIFICATE = config("FIREBASE_CERTIFICATE", cast=json.loads)
