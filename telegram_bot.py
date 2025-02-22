import telebot
import os
from flask import Flask, request
from loguru import logger

from utils.evaluator import evaluate_task
from utils.explain_grammar import explain_grammar
from utils.process_img import process_img
from utils.report import generate_report

# from utils.practice_manager import run_practice
from utils.db_models import Phrase
from utils.db import firebase_connection, add_record
from utils.config_utils import get_allowed_users
from utils.leitner import initialize_leitner

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")
ALLOWED_USERS = get_allowed_users()
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
db_client = firebase_connection()
leitner = initialize_leitner(usernames=ALLOWED_USERS, db_client=db_client)
server = Flask(__name__)
user_states = {}
last_msg_states = {}
add_states = {}
last_exercise = {}
parsed_img_states = {}


@bot.message_handler(commands=["start"])
def send_welcome(message):
    logger.info(f"Received /start command from {message.from_user.username}")

    keyboard = telebot.types.InlineKeyboardMarkup()
    practice_button = telebot.types.InlineKeyboardButton(
        text="Practice", callback_data="next_practice"
    )
    add_button = telebot.types.InlineKeyboardButton(
        text="Add phrase", callback_data="add_button"
    )

    keyboard.add(practice_button, add_button)

    bot.send_message(
        message.chat.id,
        "Oh, you finally showed up! Welcome to CrankyTutorBot, where I make sure you learn—or else.",
        reply_markup=keyboard,
    )


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    username = message.from_user.username
    language = leitner[username].user_language
    logger.info(f"Received photo from {username}")

    if username not in ALLOWED_USERS:
        bot.reply_to(
            message, "Who do you think you are? Picture upload isn’t for you. Shoo!"
        )
        logger.warning(f"Unauthorized practice attempt by user {username}")
    else:
        try:
            msg = "On it! Let me extract the phrases for you. Just a sec. I need to concentrate. brb."
            bot.send_message(chat_id=message.chat.id, text=msg)

            file_info = bot.get_file(message.photo[-1].file_id)
            logger.info(f"File info: {file_info}")

            file = bot.download_file(file_info.file_path)
            logger.info(f"Downloaded file for user {username}")

            file_path = os.path.join("data", "last_img.jpg")
            with open(file_path, "wb") as new_file:
                new_file.write(file)
            logger.info(f"Saved file to {file_path}")

            result = process_img(file_path, language)
            parsed_img_states[username] = result
            response = f"I processed the picture and extracted the following phrases: {result}. Do you want to add them?"
            keyboard = telebot.types.InlineKeyboardMarkup()
            yes_button = telebot.types.InlineKeyboardButton(
                text="Yes", callback_data="img_send_to_db"
            )
            no_button = telebot.types.InlineKeyboardButton(
                text="No", callback_data="img_fallback"
            )

            keyboard.add(yes_button, no_button)
            bot.send_message(
                chat_id=message.chat.id, text=response, reply_markup=keyboard
            )
            logger.info(f"Processed image and sent response to {username}")
        except Exception as e:
            logger.error(f"Error processing photo from {username}: {e}")
            bot.send_message(
                chat_id=message.chat.id,
                text="Sorry, something went wrong while processing the photo.",
            )


@bot.message_handler(commands=["stats"])
def get_stats(message):
    username = message.from_user.username
    logger.info(f"Received /stats command from {username}")

    if username not in ALLOWED_USERS:
        bot.reply_to(
            message, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(f"Unauthorized practice attempt by user {username}")
    else:
        stats = leitner[username].get_stats()
        bot.send_message(
            chat_id=message.chat.id,
            text=stats,
        )

    keyboard = telebot.types.InlineKeyboardMarkup()
    practice_button = telebot.types.InlineKeyboardButton(
        text="Practice", callback_data="next_practice"
    )
    add_button = telebot.types.InlineKeyboardButton(
        text="Add phrase", callback_data="add_button"
    )

    keyboard.add(practice_button, add_button)
    bot.send_message(
        chat_id=message.chat.id,
        text="Ready for the next challenge?",
        reply_markup=keyboard,
    )

    image_path = generate_report(leitner[username])

    with open(image_path, "rb") as image:
        bot.send_photo(chat_id=message.chat.id, photo=image)


@bot.callback_query_handler(func=lambda call: call.data == "img_send_to_db")
def img_send_to_db(call):
    username = call.from_user.username
    logger.info(f"User {username} clicked 'Yes' to add phrases to the database")
    keyboard = telebot.types.InlineKeyboardMarkup()
    practice_button = telebot.types.InlineKeyboardButton(
        text="Practice", callback_data="next_practice"
    )
    add_more_button = telebot.types.InlineKeyboardButton(
        text="Add more", callback_data="add_button"
    )

    keyboard.add(practice_button, add_more_button)

    phrases = parsed_img_states.get(username)
    if isinstance(phrases, list):
        for phrase in phrases:
            try:
                new_phrase = Phrase(text=phrase)
                add_record(
                    username=username,
                    data=new_phrase,
                    db_client=db_client,
                )
                bot.send_message(call.from_user.id, f"Added phrase: {phrase}")
            except Exception as e:
                logger.error(f"Error adding phrase for {username}: {e}")
                bot.send_message(call.from_user.id, f"Failed to add phrase: {phrase}")

        bot.send_message(
            call.from_user.id,
            "Well, I did my best. I added all of them. Now, let's see if you can actually translate them under pressure.",
            reply_markup=keyboard,
        )
    else:
        bot.send_message(
            call.from_user.id,
            "Well, that was a waste of time. I didn't manage to add any phrases. What a shame.",
            reply_markup=keyboard,
        )


@bot.callback_query_handler(func=lambda call: call.data == "img_fallback")
def img_fallback(call):
    username = call.from_user.username
    logger.info(f"User {username} clicked 'No' to add phrases to the database")
    parsed_img_states[username] = None
    keyboard = telebot.types.InlineKeyboardMarkup()
    practice_button = telebot.types.InlineKeyboardButton(
        text="Practice", callback_data="next_practice"
    )
    add_button = telebot.types.InlineKeyboardButton(
        text="Add phrase", callback_data="add_button"
    )
    keyboard.add(practice_button, add_button)
    bot.send_message(
        call.from_user.id,
        "Fine, I won't add them. Whatever. You're the boss. For now.",
        reply_markup=keyboard,
    )


@bot.message_handler(commands=["add"])
def add(message):
    username = message.from_user.username
    logger.info(f"Received /add command from {message.from_user.username}")
    if username not in ALLOWED_USERS:
        bot.reply_to(
            message, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(
            f"Unauthorized practice attempt by user {message.from_user.username}"
        )
        return
    else:
        logger.info(
            f"Adding new phrase for {message.from_user.username}: {message.text}"
        )

        new_phrase = Phrase(text=message.text.split("/add ")[1])

        add_record(
            username=username,
            data=new_phrase,
            db_client=db_client,
        )

        logger.info(f"Added phrase: {new_phrase.text}")

        keyboard = telebot.types.InlineKeyboardMarkup()
        practice_button = telebot.types.InlineKeyboardButton(
            text="Practice", callback_data="next_practice"
        )
        add_more_button = telebot.types.InlineKeyboardButton(
            text="Add more", callback_data="add"
        )

        keyboard.add(practice_button, add_more_button)

        bot.send_message(
            message.chat.id,
            "Fine, added it. Next time take an image. It's faster, more efficient, and less annoying.",
            reply_markup=keyboard,
        )


@bot.message_handler(commands=["practice"])
def practice(message):
    username = message.from_user.username
    if username not in ALLOWED_USERS:
        bot.reply_to(
            message, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(
            f"Unauthorized practice attempt by user {message.from_user.username}"
        )
        return
    else:
        try:
            task = leitner[username].gen_translation_task()
            task_text = task.translation
            task_type = "Translate"
            logger.info(f"Task generated: {task_text}")
            bot.reply_to(message, f"{task_type}: {task}")
            last_exercise[message.from_user.id] = task_type
            user_states[message.from_user.id] = task
        except Exception as e:
            logger.error(f"Error during practice: {e}")


@bot.message_handler(func=lambda message: True)
def respond_to_text(message):
    user_id = message.from_user.id
    username = message.from_user.username
    user_msg = message.text
    task = user_states.get(user_id)
    task_desc = last_exercise.get(user_id)

    if username not in ALLOWED_USERS:
        bot.reply_to(
            message, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(f"Unauthorized practice attempt by user {username}")
        return
    elif user_states.get(user_id):
        logger.info(f"User {username} submitted translation: {user_msg}")

        evaluation = evaluate_task(
            user_response=user_msg, test_phrase=task.translation, task_desc=task_desc
        )
        bot.reply_to(message, evaluation["evaluation_text"])

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)

        explain_button = telebot.types.InlineKeyboardButton(
            text="Explain", callback_data="explain_callback"
        )
        next_practice_button = telebot.types.InlineKeyboardButton(
            text="Next Practice", callback_data="next_practice"
        )

        keyboard.add(explain_button, next_practice_button)

        if evaluation["evaluation_outcome"] == 1:
            success_msg = leitner[username].add_correct_answer(phrase_id=task.phrase_id)
            if success_msg:
                bot.send_message(
                    message.chat.id,
                    success_msg,
                )
        else:
            leitner[username].add_mistake(phrase_id=task.phrase_id)

        bot.send_message(
            message.chat.id, "Ready for the next challenge?", reply_markup=keyboard,
        )

        user_states[user_id] = None
        last_msg_states[user_id] = task

    elif add_states.get(user_id):
        logger.info(f"User {username} added phrase: {user_msg}")
        new_phrase = Phrase(text=user_msg)
        add_record(
            username=username,
            data=new_phrase,
            db_client=db_client,
        )
        logger.info(f"Added phrase: {user_msg}")
        keyboard = telebot.types.InlineKeyboardMarkup()
        practice_button = telebot.types.InlineKeyboardButton(
            text="Practice", callback_data="next_practice"
        )
        add_more_button = telebot.types.InlineKeyboardButton(
            text="Add more", callback_data="add_button"
        )
        keyboard.add(practice_button, add_more_button)

        bot.send_message(
            message.chat.id,
            "Fine, added it. Next time take an image. It's faster, more efficient, and less annoying.",
            reply_markup=keyboard,
        )
        add_states[message.from_user.id] = None
    else:
        logger.info(f"User {username} added phrase: {user_msg}")
        new_phrase = Phrase(text=message.text.split("/add ")[1])

        add_record(
            username=username,
            data=new_phrase,
            db_client=db_client,
        )
        logger.info(f"Added phrase: {new_phrase.text}")
        keyboard = telebot.types.InlineKeyboardMarkup()
        practice_button = telebot.types.InlineKeyboardButton(
            text="Practice", callback_data="next_practice"
        )

        add_more_button = telebot.types.InlineKeyboardButton(
            text="Add phrase", callback_data="add_button"
        )
        keyboard.add(practice_button, add_more_button)

        bot.send_message(
            message.chat.id,
            f"Did you really just say {message.text}? Well, you're not in a practice session right now. Use *practice* command to start.",
            reply_markup=keyboard,
        )


@bot.callback_query_handler(func=lambda call: call.data == "next_practice")
def handle_next_practice(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logger.info(f"User {username} clicked 'Next Practice'")
    if username not in ALLOWED_USERS:
        bot.reply_to(
            call, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(
            f"Unauthorized practice attempt by user {call.from_user.username}"
        )
        return
    else:
        try:
            task = leitner[username].gen_translation_task()
            task_text = task.translation
            task_type = "Translate"
            logger.info(f"Task generated: {task_text}")
            bot.send_message(user_id, f"{task_type}: {task_text}")
            last_exercise[call.from_user.id] = task_type
            user_states[call.from_user.id] = task
        except Exception as e:
            logger.error(f"Error during practice: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "explain_callback")
def handle_explain_button(call):
    user_id = call.from_user.id
    username = call.from_user.username
    language = leitner[username].user_language if username in leitner else 'Spanish'
    logger.info(f"User {username} clicked 'Explain' button with language {language}")

    keyboard = telebot.types.InlineKeyboardMarkup()

    next_practice_button = telebot.types.InlineKeyboardButton(
        text="Next Practice", callback_data="next_practice"
    )
    add_button = telebot.types.InlineKeyboardButton(
        text="Add phrase", callback_data="add_button"
    )

    keyboard.add(add_button, next_practice_button)

    if username not in ALLOWED_USERS:
        bot.reply_to(
            call, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(
            f"Unauthorized practice attempt by user {call.from_user.username}"
        )
    else: 
        last_msg = last_msg_states.get(user_id)

        if last_msg:
            correct_response = last_msg.text
            explanation = explain_grammar(
                language=language, correct_response=correct_response
            )
            logger.info(f"Generated explanation for user {username}: {explanation}")

            try:
                explanation = f"Correct response: *{correct_response}*\n\n{explanation}"
                bot.send_message(
                user_id,
                explanation,
                reply_markup=keyboard,
            )
            except Exception as e:
                explanation = f"I don't have any good explanation for you. What a shame. But at least I can tell you that the correct answer is:*{correct_response}*. Try to remember it, okay? Even if you don't want to. Just do it."

                explain_grammar.cache_clear()

                bot.send_message(
                user_id,
                explanation,
                reply_markup=keyboard,
                )
                logger.error(f"Failed to generate explanation for user {username}: {e}")
        else:
            bot.send_message(
                user_id,
                "Something or someone terribly messed up. I can't find the last message. I'm not happy about it. But I'm not going to do anything about it. Just so you know.",
                reply_markup=keyboard,
            )


@bot.callback_query_handler(func=lambda call: call.data == "add_button")
def handle_add_button(call):
    user_id = call.from_user.id
    username = call.from_user.username
    logger.info(f"User {username} clicked 'Add phrase' button")

    if username not in ALLOWED_USERS:
        bot.reply_to(
            call, "Who do you think you are? This feature isn’t for you. Shoo!"
        )
        logger.warning(
            f"Unauthorized practice attempt by user {call.from_user.username}"
        )
    else:
        bot.send_message(
            user_id, "Provide me a phrase to work with. Don't keep it waiting."
        )
        add_states[user_id] = 1


@server.route("/" + TOKEN, methods=["POST"])
def getMessage():
    try:
        msg = request.stream.read().decode("utf-8")
        logger.info(f"Received a new message from Telegram: {msg}")
        bot.process_new_updates([telebot.types.Update.de_json(msg)])
        return "!", 200
    except Exception as e:
        logger.error(f"Error processing the message: {e}")
        return "Internal Server Error", 500


@server.route("/")
def webhook():
    try:
        logger.info("Setting up webhook.")
        bot.remove_webhook()
        bot.set_webhook(url=f"https://{HEROKU_APP_NAME}.herokuapp.com/" + TOKEN)
        return "!", 200
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return "Internal Server Error", 500


if __name__ == "__main__":
    logger.info("Starting server...")
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
