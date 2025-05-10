from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv("EMAIL")
secret_key = os.getenv("EMAIL_PASSWORD")
debug_mode = os.getenv("DEBUG")

print(f"Database URL: {database_url}")
print(f"Secret Key: {secret_key}")
print(f"Debug Mode: {debug_mode}")