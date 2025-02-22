from abc import ABC, abstractmethod
import os

import openai
import google.generativeai as genai


class ModelInterface(ABC):
    @abstractmethod
    def configure(self):
        pass

    @abstractmethod
    def generate_response(self, system_prompt, user_prompt, **kwargs):
        pass


class OpenAIModel(ModelInterface):
    def configure(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )

    def generate_response(self, system_prompt, user_prompt, **kwargs):
        if system_prompt:
            system_msg = [{"role": "system", "content": system_prompt}]
        else:
            system_msg = []
        if user_prompt:
            user_msg = [{"role": "user", "content": user_prompt}]
        else:
            user_msg = []

        msgs = system_msg + user_msg

        response = self.client.chat.completions.create(
            model=kwargs.get("model_name", "gpt-4o-mini"),
            temperature=kwargs.get("temperature", 0.7),
            response_format=kwargs.get("response_format", None),
            messages=msgs,
        )

        clean_response = response.choices[0].message.content.strip().replace('"', "'")
        return clean_response


class GoogleModel(ModelInterface):
    def configure(self):
        genai.configure(api_key=os.getenv("GOOGLE_AI_STUDIO_KEY"))

    def generate_response(self, system_prompt, **kwargs):
        model = genai.GenerativeModel(
            model_name=kwargs.get("model_name", "gemini-2.0-flash-exp"),
            system_instruction=system_prompt,
        )
        chat = model.start_chat()
        response = chat.send_message(system_prompt)
        clean_response = response.text.strip().replace('"', "'")
        return clean_response


def get_model(model_type):
    if model_type == "openai":
        model = OpenAIModel()
        model.configure()
        return model
    elif model_type == "google":
        model = GoogleModel()
        model.configure()
        return model
    else:
        raise ValueError(f"Unknown model type: {model_type}")
