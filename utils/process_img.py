import openai
import os
import base64
import logging

API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY


def encode_img(image_path):
    logging.info(f"Encoding image: {image_path}")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def process_img(file, language):
    logging.info(f"Processing image: {file} for language: {language}")

    base64_image = encode_img(file)

    system_instruction = f"""You are given an image with phrases or keywords to extract.

    Create a python list of complete sentences in {language}, based on extracted information.

    - If you find a standalone word, complete it into a full sentence by extending it with vocabulary of your choice.
    - If you find a full sentence, take that sentence as is
    - Skip any irrelevant words that is not useful for creating sentences.
    - Skip any grammatical descriptions or instructions in the image.

    For example, if you see word "sun" in the image, you should create a sentence "The sun rises in the east" in {language} and add it to the list. If you see a full sentence "The sun goes down", you should add it to the list as is. If you see word "have risen (past)", you should just extract "have risen" and skip the "(past)" part.

    The individual strings in your output should be in {language} language.

    Be exhaustive (do not skip any phrases) and do not add any extra phrases that are not in the image."""

    try:
        client = openai.OpenAI()
        logging.info("Sending request to OpenAI API")
        # Send the image and prompt to the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "llm_evaluation",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "extracted_sentences": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Extracted full sentences from the image. Be exhaustive. Only",
                            },
                            "extracted_keywords": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "All additional keywords or incomplete sentences present in the image, that were not part of the extracted sentences. Be exhaustive here.",
                            },
                            "completed_sentences": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Completed sentences from every extracted keyword in field extracted_keywords, that is relevant to learning the language. Do not skip any relevant keywords or their variations.",
                            },
                        },
                        "required": [
                            "extracted_sentences",
                            "extracted_keywords",
                            "completed_sentences",
                        ],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
            messages=[
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "Give me a python list of complete sentences, each containing a phrase in {language}, using the vocabulary or phrases in the image",
                        },
                    ],
                },
            ],
        )
        logging.info("Received response from OpenAI API")

        try:
            extracted_sentences = eval(response.choices[0].message.content)[
                "extracted_sentences"
            ]
            logging.info(f"Extracted sentences: {extracted_sentences}")
        except Exception as e:
            logging.error(f"Error extracting sentences: {e}")
            extracted_sentences = []

        try:
            completed_sentences = eval(response.choices[0].message.content)[
                "completed_sentences"
            ]
            logging.info(f"Completed sentences from keywords: {completed_sentences}")
        except Exception as e:
            logging.error(f"Error comppleting sentences: {e}")
            completed_sentences = []

        combined_sentences = extracted_sentences + completed_sentences
        return combined_sentences
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return f"Error processing image: {e}"


if __name__ == "__main__":
    language = "Czech"
    result = process_img("test.png", language)
    logging.info(f"Result: {result}")
    print(result)
