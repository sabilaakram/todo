#to make our url secret we use:
from starlette.datastructures import Secret
from starlette.config import Config

try:
    config = Config(".env")

except FileNotFoundError:
    config = Config()

DATABASE_URL = config("DATABASE_URL", cast=Secret)