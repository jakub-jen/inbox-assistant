from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    input="Odpověz pouze větou: AI připojení funguje.",
    reasoning={"effort": "none"},
)

print(response.output_text)