import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Say hello in one short sentence"
)

print(response.output_text)