import random
from loguru import logger
import google.generativeai as genai
import os

API_KEY = os.getenv("GOOGLE_AI_STUDIO_KEY")
genai.configure(api_key=API_KEY)


def gen_case_identification_task(user_language="Czech"):
    logger.info(f"Identifying case for language: {user_language}")

    case_or_preposition = draw_case_or_preposition(user_language=user_language)
    logger.info(f"Selected case or preposition: {case_or_preposition}")

    system_instruction = f"""Your task is to create a simple sentence using {case_or_preposition} in {user_language}. Respond with the sentence only, do not explain yourself. The user will have to guess the grammatical case used. Use basic vocabulary and always include subject, verb, and object in your sentence."""

    try:
        model = genai.GenerativeModel(
            "gemini-2.0-flash-exp", system_instruction=system_instruction
        )
        chat = model.start_chat()
        response = chat.send_message(system_instruction)
        logger.info("Successfully generated verb declination prompt.")
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating verb declination: {e}")


def draw_case_or_preposition(user_language="Czech"):
    logger.info(f"Drawing case or preposition for language: {user_language}")

    cases = {
        "Czech": {
            "nominative": [],
            "genitive": [
                "od",
                "do",
                "z",
                "bez",
                "u",
                "kromě",
                "vedle",
                "místo",
                "kolem",
                "podle",
                "během",
                "za",
            ],
            "dative": [
                "k",
                "ke",
                "proti",
                "naproti",
                "vůči",
                "kvůli",
            ],
            "accusative": [
                "pro",
                "mimo",
                "skrz",
                "přes",
                "o",
                "na",
                "v",
                "po",
                "před",
                "nad",
                "pod",
                "mezi",
                "za",
            ],
            "locative": [
                "v",
                "ve",
                "o",
                "na",
                "po",
            ],
            "instrumental": [
                "s",
                "za",
                "před",
                "nad",
                "pod",
                "mezi",
            ],
        }
    }

    def draw_preposition_with_case(user_language, cases):
        prepositions_with_cases = [
            (preposition, case)
            for case, prepositions in cases[user_language].items()
            for preposition in prepositions
        ]
        return random.choice(prepositions_with_cases)

    if random.random() < 0.5:
        selected_case = random.choice(list(cases[user_language].keys()))
        logger.info(f"Selected case: {selected_case}")
        return selected_case
    else:
        selected_preposition, selected_case = draw_preposition_with_case(
            user_language, cases
        )
        logger.info(f"Selected preposition: {selected_preposition} ({selected_case})")
        logger.info(f"Selected preposition: {selected_preposition}")
        return f"preposition '{selected_preposition}' in {selected_case} case"


if __name__ == "__main__":
    logger.info("Starting the case identification process.")
    phrase = gen_case_identification_task(user_language="Czech")
    logger.info(f"Generated phrase: {phrase}")
