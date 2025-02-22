import uuid

from firebase_admin import firestore
from loguru import logger
from pydantic import BaseModel, Field
from typing import Optional, Any, ClassVar, Type, Dict

from utils.models import get_model


class Phrase(BaseModel):
    COLLECTION_NAME: ClassVar[str] = "phrases"
    text: str
    phrase_id: Optional[str] = None
    translation: Optional[str] = None
    leitner_stage: int = Field(default=0, ge=0, le=5)
    leitner_current: bool = False
    mistakes: int = 0
    correct_answers: int = 0
    created_at: Optional[Any] = Field(
        default_factory=lambda: firestore.SERVER_TIMESTAMP
    )
    updated_at: Optional[Any] = Field(
        default_factory=lambda: firestore.SERVER_TIMESTAMP
    )

    def __init__(self, **data):
        super().__init__(**data)
        if self.translation is None:
            self.translation = translate_to_base_lang(self.text)
        if self.phrase_id is None:
            self.phrase_id = uuid.uuid4().hex[:20]

    def add_correct_answer(self):
        if self.leitner_stage < 5:
            self.leitner_stage += 1
        if self.leitner_stage == 5:
            self.leitner_current = False
        self.correct_answers += 1
        self.updated_at = firestore.SERVER_TIMESTAMP

    def add_mistake(self):
        self.leitner_stage = 1
        self.mistakes += 1
        self.updated_at = firestore.SERVER_TIMESTAMP


class User(BaseModel):
    COLLECTION_NAME: ClassVar[str] = "users"
    language: str
    created_at: Optional[Any] = Field(
        default_factory=lambda: firestore.SERVER_TIMESTAMP
    )


collection_class_map: Dict[str, Type[BaseModel]] = {
    Phrase.COLLECTION_NAME: Phrase,
    User.COLLECTION_NAME: User,
}


def translate_to_base_lang(text: str, base_lang: str = "English") -> Optional[str]:
    logger.info(f"Translating text: '{text}' to base language: '{base_lang}'")
    system_instruction = f"""You are an assistant that generates translations for language learning purposes, by translating an input phrase to {base_lang}. If the input is already in {base_lang}, just respond with the same phrase."""

    model = get_model("openai")
    user_instruction = f'Input Phrase: "{text}"\nTranslation:'

    try:
        response = model.generate_response(
            system_prompt=system_instruction,
            user_prompt=user_instruction,
            model_name="gpt-4o-mini",
        )
        logger.info(f"Translation successful: '{response}'")
        return response

    except Exception as e:
        logger.error(f"Error generating translation: {e}")
        return None
