from functools import lru_cache

from loguru import logger

from utils.models import get_model


@lru_cache(maxsize=50)
def explain_grammar(
    language,
    correct_response,
    model_type="google",
    model_name="gemini-2.0-flash-lite-preview-02-05",
):
    logger.info(f"Explaining grammar for {correct_response}")

    prompt = f"""You are CrankyTutorBot, a no-nonsense language tutor of {language} with a strict but fair attitude. Explain the grammatical concepts used in the phrase '{correct_response}'. Respond with this structure:

    *Grammar*: Briefly explain the 1-2 most relevant grammar concepts of {language} that are used in this phrase. For example, you may name the cases used, e.g., Vocativ (Case 5), explain the verb conjugations or noun declensions, if applicable. Strive for conciseness and clarity in your explanation. Neither you nor the student have all day.

    *Examples*: Give 1-2 other examples to illustrate usage of the key grammar concepts in different scenarios."""

    model = get_model(model_type)

    try:
        return model.generate_response(prompt, model_name=model_name)

    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        return {"evaluation_text": "Error during evaluation.", "evaluation_outcome": 0}

