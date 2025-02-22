import random
from loguru import logger
from utils import db
import openai
import os

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
client = openai.OpenAI(api_key=API_KEY, base_url=BASE_URL)


def gen_verb_conjugation_task(username, db_client, language="English", tense="past"):
    verb = query_verb_from_db(username, db_client)
    if verb is None:
        logger.info("No verb provided. Creating random verb sentence.")

        system_instruction = f"""
        You are an assistant that helps language learners practice verb declination. 
        Task:
        Choose a random verb in {language}, then create a simple sentence with a blank for the verb in the {tense} tense, where the user is supposed to fill in the correct verb.
        Answer only with a sentence in the format: noun-blank-subject, and nothing else.
        For example: "The lady [...] an apple. (eat, past)" or "The teacher [...] (smile, present)" 
        Always use [...] to indicate blank and always put the infinitive form  + expected tense in the bracket." 
        Remember, your example must be in {language}."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": system_instruction}],
                temperature=0.7,
            )
            logger.info("Successfully generated verb declination prompt.")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating verb declination: {e}")
            return None
    else:
        logger.info(f"Verb provided: {verb}. Creating declination sentence.")

        system_instruction = f"""
        You are an assistant that helps language learners practice verb declination. 
        Task:
        Create a simple sentence with a blank for the verb in the {tense} tense, where the user is supposed to fill in the correct verb.
        Use the verb '{verb}'.
        Answer only with a sentence in the format: noun-blank-subject, and nothing else.
        For example: "The lady [...] an apple. (eat, past)" or "The teacher [...] (smile, present)" 
        Always use [...] to indicate blank and always put the infinitive form  + expected tense in the bracket." 
        Remember, your example must be in {language}."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": system_instruction}],
                temperature=0.7,
            )
            logger.info("Successfully generated verb declination prompt.")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating verb declination: {e}")
            return None


def query_verb_from_db(username, db_client):
    if random.random() < 0.2:
        logger.info("20% chance hit: Returning None.")
        return None

    try:
        selected_verb = db.get_random_document(username, "verbs", db_client)["verb"]
        logger.info(
            f"Successfully retrieved verb: {selected_verb} for user: {username}"
        )

        if (
            isinstance(selected_verb, str)
            and selected_verb.isalpha()
            and " " not in selected_verb
        ):
            logger.info(f"Valid verb selected: {selected_verb}")
            return selected_verb
        else:
            logger.warning("Retrieved verb is not a valid single word.")
            return None
    except Exception as e:
        logger.error(
            f"Failed to retrieve a random verb for user: {username}. Error: {e}"
        )
        return None
