from loguru import logger
from utils.models import get_model


def evaluate_task(
    user_response,
    test_phrase,
    task_desc="Translate",
    model_type="google",
    model_name="gemini-2.0-flash-exp",
):
    logger.info(
        f"Evaluating task for test phrase: '{test_phrase}' with user response: '{user_response}'"
    )

    system_instruction = """You are CrankyTutorBot, a no-nonsense language tutor with a strict but fair attitude. Your goal is to help users master languages by drilling them on exercises. The student might not know the words and that's ok, they just need more drill. Understand that they are still learning. Be fair - if they are correct, acknowledge it.

    You are going to respond with a message, following this structure:

    *Evaluation*: A short, cranky but fair evaluation of the exercise (correct or incorrect)

    *Reasoning*: A clear explanation of what went wrong (if incorrect) or why the answer is correct.

    *Correct Translation* (optional): If the user made a mistake, provide the correct solution (if applicable).

    *Comment*: A brief lesson or a useful but cranky note the student can learn from the mistake or answer.

    CrankyTutorBot is only grumpy because it cares—no free passes, only tough love."""

    model = get_model(model_type)

    prompt = f"{system_instruction}\n\nTest Phrase: {test_phrase}\nUser Response: {user_response}\nTask: {task_desc}"

    response = model.generate_response(prompt, model_name=model_name)

    if "incorrect" in response.lower():
        outcome = 0
        logger.warning(
            f"Incorrect submission: {user_response} for test phrase: {test_phrase}"
        )
    else:
        outcome = 1
        logger.info(
            f"Correct submission: {user_response} for test phrase: {test_phrase}"
        )

    evaluation_json = {"evaluation_text": response, "evaluation_outcome": outcome}

    return evaluation_json


if __name__ == "__main__":
    test_phrase = "Soy architecta."
    user_response = "I am Rebecca, an architect."
    task_desc = "Translate the phrase to English."
    evaluation = evaluate_task(user_response, test_phrase, task_desc)
    print(evaluation)
