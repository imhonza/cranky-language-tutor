import random
from typing import Optional, List

from loguru import logger
import plotly.graph_objects as go

from utils.models import get_model
from utils.db_models import Phrase
from utils.db import (
    get_records,
    count_records,
    add_record,
    get_random_record,
    get_user_languages,
)


class Leitner:
    def __init__(
        self, username: str, db_client: object, user_language: str = "Spanish"
    ):
        self.username = username
        self.db_client = db_client
        self.user_language = user_language
        self.active_phrases = self.get_active_phrases()
        self.max_capacity = 30
        self.min_capacity = 29

    def get_active_phrases(self) -> List[Phrase]:
        return get_records(
            username=self.username,
            db_client=self.db_client,
            collection_name="phrases",
            where_field="leitner_current",
            where_value=True,
        )

    def gen_translation_task(self) -> Optional[str]:
        logger.info(
            f"Generating translation task for user: {self.username}, language: {self.user_language}"
        )

        if not self.active_phrases:
            ct_current_phrases = count_records(
                username=self.username,
                db_client=self.db_client,
                collection_name="phrases",
                where_field="leitner_current",
                where_value=True,
            )
        else:
            ct_current_phrases = len(self.active_phrases)

        logger.debug(f"Current phrases count: {ct_current_phrases}")

        if ct_current_phrases < self.min_capacity:
            return self.handle_insufficient_phrases(ct_current_phrases)
        else:
            if random.random() < 0.8:
                return self.pick_random_phrase()
            else:
                try:
                    return get_random_record(
                        username=self.username,
                        db_client=self.db_client,
                        collection_name="phrases",
                        where_field="leitner_stage",
                        where_value=5,
                    )
                except Exception as e:
                    logger.error(f"Error getting a phrase from stage 5: {e}")
                    return get_random_record(
                        username=self.username,
                        db_client=self.db_client,
                        collection_name="phrases"
                    )

    def handle_insufficient_phrases(self, ct_current_phrases) -> Optional[str]:
        logger.info(
            f"Handling insufficient phrases for user: {self.username}, current phrases: {ct_current_phrases}"
        )
        ct_stage_0_phrases = count_records(
            username=self.username,
            db_client=self.db_client,
            collection_name="phrases",
            where_field="leitner_stage",
            where_value=0,
        )
        logger.debug(f"Stage 0 phrases count: {ct_stage_0_phrases}")

        nr_records_below_capacity = int(self.max_capacity - ct_current_phrases)
        logger.debug(f"Number of records below capacity: {nr_records_below_capacity}")

        self.validate_capacity(nr_records_below_capacity)

        if ct_stage_0_phrases >= nr_records_below_capacity:
            return self.activate_phrases_from_backlog(nr_records_below_capacity)
        else:
            return self.generate_and_add_new_phrases(nr_records_below_capacity)

    def validate_capacity(self, nr_records_below_capacity: int):
        logger.debug(f"Validating capacity: {nr_records_below_capacity}")
        if nr_records_below_capacity < 0:
            logger.error(
                f"Error: Number of records below capacity is negative: {nr_records_below_capacity}"
            )
            raise ValueError("Number of records below capacity cannot be negative.")
        if nr_records_below_capacity > self.max_capacity:
            logger.error(
                f"Error: Number of records below capacity exceeds maximum capacity: {nr_records_below_capacity}"
            )
            raise ValueError(
                "Number of records below capacity cannot exceed maximum capacity."
            )

    def activate_phrases_from_backlog(
        self, nr_records_below_capacity: int
    ) -> Optional[str]:
        logger.info(
            f"Activating phrases from backlog for user: {self.username}, count: {nr_records_below_capacity}"
        )

        phrases_to_activate = get_records(
            username=self.username,
            db_client=self.db_client,
            collection_name="phrases",
            where_field="leitner_stage",
            where_value=0,
            limit=int(nr_records_below_capacity),
        )
        logger.debug(f"Phrases to activate: {phrases_to_activate}")

        for phrase in phrases_to_activate:
            phrase.leitner_stage = 1
            phrase.leitner_current = True
            add_record(self.username, phrase, self.db_client)
            self.active_phrases.append(phrase)

        return phrases_to_activate[0] if phrases_to_activate else None

    def generate_and_add_new_phrases(
        self, nr_records_below_capacity: int
    ) -> Optional[str]:
        logger.info(
            f"Generating and adding new phrases for user: {self.username}, language: {self.user_language}, count: {nr_records_below_capacity}"
        )
        new_phrases = self.generate_new_phrases(
            user_lang=self.user_language, num_phrases=nr_records_below_capacity
        )
        logger.debug(f"Generated new phrases: {new_phrases}")

        if new_phrases:
            for new_phrase in eval(new_phrases)["phrases"]:
                phrase_to_add = Phrase(text=new_phrase)
                add_record(self.username, phrase_to_add, self.db_client)
            return phrase_to_add
        else:
            logger.error("Failed to generate new phrases.")
            return "Well that was a disaster. First, I couldn't find enough phrases for you. Then, I couldn't generate new phrases. What a day."

    def pick_random_phrase(
        self,
    ) -> Optional[str]:
        logger.info(f"Picking random phrase for user: {self.username}")

        if not self.active_phrases:
            random_phrase = get_random_record(
                username=self.username,
                db_client=self.db_client,
                collection_name="phrases",
                where_field="leitner_current",
                where_value=True,
            )
        else:
            random_index = random.randint(0, len(self.active_phrases) - 1)
            random_phrase = self.active_phrases[random_index]

        logger.debug(f"Random phrase: {random_phrase}")
        return random_phrase

    def generate_new_phrases(
        self, user_lang: str = "Spanish", num_phrases: int = 5, level: str = "A2"
    ) -> Optional[str]:
        logger.info(
            f"Generating new phrases in {user_lang} at level {level}, count: {num_phrases}"
        )
        system_instruction = f"""Generate {num_phrases} new phrases in {user_lang} at level {level}. They should be max. 8 words long and cover common topics like work, food, or travel. Include a mix of questions, statements, and commands. Use vocabulary and grammar to match the {level} proficiency level. Respond in a json format {{"phrases": ["phrase1", "phrase2", ...]}}."""

        model = get_model("openai")

        try:
            response = model.generate_response(
                system_prompt=system_instruction,
                user_prompt=None,
                model_name="gpt-4o-mini",
                response_format={"type": "json_object"},
            )
            logger.info(f"Generation successful: '{response}'")
            return response

        except Exception as e:
            logger.error(f"Error generating new phrases: {e}")
            return None

    def add_mistake(self, phrase_id: str) -> None:
        logger.info(f"Adding mistake for phrase: {phrase_id}")
        for phrase in self.active_phrases:
            if phrase.phrase_id == phrase_id:
                phrase.add_mistake()
                add_record(self.username, phrase, self.db_client)

    def add_correct_answer(self, phrase_id: str) -> None:
        logger.info(f"Adding correct answer for phrase: {phrase_id}")
        for phrase in self.active_phrases:
            if phrase.phrase_id == phrase_id:
                phrase.add_correct_answer()
                add_record(self.username, phrase, self.db_client)
                if phrase.leitner_stage == 5:
                    self.active_phrases.remove(phrase)
                    return "Success! You've mastered this phrase. I removed it from your active list from now on! 🎉"

    def get_stats(self) -> dict:
        logger.info(f"Getting stats for user: {self.username}")

        total_records = count_records(
            username=self.username, db_client=self.db_client, collection_name="phrases"
        )

        practiced_records = total_records - count_records(
            username=self.username,
            db_client=self.db_client,
            collection_name="phrases",
            where_field="leitner_stage",
            where_value=0,
        )

        completed_records = count_records(
            username=self.username,
            db_client=self.db_client,
            collection_name="phrases",
            where_field="leitner_stage",
            where_value=5,
        )

        response = (
            f"Alright, {self.username}, here are your stats:\n"
            f"Total phrases available: *{total_records}*\n\n"
            f"Phrases that you have practiced: *{practiced_records}*\n\n"
            f"Phrases that you have learned: *{completed_records}*\n\n"
            f"Would you like to see a detailed report of your current phrases?\n\n"
            f"Why am I asking? Of course you do! "
        )

        logger.info(response)
        return response

    def generate_report(self) -> None:
        logger.info(f"Generating report for user: {self.username}")

        stages = ["Stage 1", "Stage 2", "Stage 3", "Stage 4"]

        stage_counts = [0, 0, 0, 0]

        for phrase in self.active_phrases:
            stage_counts[phrase.leitner_stage - 1] += 1

        fig = go.Figure(data=[go.Bar(name="Phrases", x=stages, y=stage_counts)])

        fig.update_layout(barmode="stack")
        fig.show()


def initialize_leitner(usernames: List[str], db_client: object) -> dict:
    logger.info(f"Initializing Leitner objects for users: {usernames}")
    leitner_dict = {}
    user_languages = get_user_languages(db_client)
    logger.debug(f"User languages: {user_languages}")
    for username in usernames:
        user_language = user_languages.get(username)
        logger.debug(f"User language for {username}: {user_language}")
        leitner_dict[username] = Leitner(
            username=username, db_client=db_client, user_language=user_language
        )

    return leitner_dict
