import dotenv
import app.constants as constants

dotenv.load_dotenv()

TORTOISE_ORM = {
    "connections": {
        "default": constants.DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": ["app.models.model", "aerich.models"],
            "default_connection": "default",
        },
    },
}
