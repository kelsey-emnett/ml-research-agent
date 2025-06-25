from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import yaml


class OpenAIChat:
    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_VERSION")
        config_path = os.path.join("./app/config", "config.yaml")

        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        self.model_name = config["openai"]["model_name"]
        self.max_tokens = config["openai"]["max_tokens"]
        self.temperature = config["openai"]["temperature"]

    def initialize_openai_client(self):
        client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
        )

        return client

    def construct_model_input(self, system_message: str, user_message: str):
        if system_message is None or user_message is None:
            raise ValueError("Both system_message and user_message are required.")

        if system_message == "" or user_message == "":
            raise ValueError("Both system_message and user_message cannot be empty.")

        model_input = [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        return model_input

    def chat(self, system_message: str, user_message: str):
        try:
            client = self.initialize_openai_client()

            model_input = self.construct_model_input(system_message, user_message)

            response = client.chat.completions.create(
                messages=model_input,
                max_completion_tokens=self.max_tokens,
                temperature=self.temperature,
                model=self.model_name,
            )

            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI API Error: {str(e)}")
