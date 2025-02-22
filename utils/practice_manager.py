import random

from loguru import logger

from utils.translate import gen_translation_task
from utils.conjugate_verbs import gen_verb_conjugation_task
from utils.identify_case import gen_case_identification_task
from utils.config_utils import load_config
from utils.phrase_variation import generate_variation


def run_practice(user_language, username, db_client, initial=True):
    config = load_config()
    enabled_features = config["languages"].get(user_language.lower(), [])

    if not enabled_features:
        raise ValueError(f"No enabled features found for language: {user_language}")

    feature = random.choice(enabled_features)
    feature = "translate"
    if feature == "translate":
        task_desc = "Translate"
        phrase = gen_translation_task(username, db_client)
        logger.info(f"Phrase selected for translation: {phrase}")
        variation = generate_variation(phrase=phrase, initial=initial)
        logger.info(f"Variation generated: {variation}")
        return variation, task_desc
    elif feature == "conjugate_verbs":
        task_desc = "Fill in the blank"
        return gen_verb_conjugation_task(
            username, db_client, language=user_language
        ), task_desc
    elif feature == "identify_case":
        task_desc = "Identify the grammatical case"
        return gen_case_identification_task(user_language), task_desc
    else:
        raise ValueError(f"Unknown feature: {feature}")
