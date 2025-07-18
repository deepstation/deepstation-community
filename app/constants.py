import os
import dotenv

dotenv.load_dotenv()

### Database ###
DATABASE_URL = os.getenv("DATABASE_URL")

### OpenAI ###
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

### Twilio ###
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

LUMA_API_KEY = os.getenv("LUMA_API_KEY")