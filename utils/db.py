import os
import random
from typing import Optional, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore
from loguru import logger

from utils.config_utils import get_allowed_users
from utils.db_models import User, collection_class_map, BaseModel


def firebase_connection() -> firestore.Client:
    logger.info("Initializing Firebase...")
    try:
        cred = credentials.Certificate(eval(os.environ["FIREBASE_CREDENTIALS"]))
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized.")
        db_client = firestore.client()
        logger.info("Firestore client created.")
        return db_client
    except (ValueError, KeyError, firebase_admin.exceptions.FirebaseError) as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise


def add_record(username: str, data: BaseModel, db_client: firestore.Client) -> None:
    logger.info(
        f"Adding record for user: {username}, collection: {data.COLLECTION_NAME}"
    )
    try:
        ref = (
            db_client.collection(User.COLLECTION_NAME)
            .document(username)
            .collection(data.COLLECTION_NAME)
            .document(data.phrase_id)
        )
        ref.set(data.model_dump())
        logger.info(f"Added {data} to {data.COLLECTION_NAME} for {username}")
    except firebase_admin.exceptions.FirebaseError as e:
        logger.error(
            f"Failed to add to {data.COLLECTION_NAME} for {username}. Error: {e}"
        )


def get_records(
    username: str,
    db_client: firestore.Client,
    collection_name: Optional[str] = None,
    where_field: Optional[str] = None,
    where_value: Optional[Any] = None,
    limit: Optional[int] = None,
) -> Dict[str, BaseModel]:
    logger.info(
        f"Retrieving records for user: {username}, collection: {collection_name}"
    )
    doc_list = []

    try:
        ref = db_client.collection(User.COLLECTION_NAME).document(username)
        if collection_name:
            ref = ref.collection(collection_name)
            if where_field and where_value is not None:
                logger.info(f"Applying filter: {where_field} == {where_value}")
                ref = ref.where(where_field, "==", where_value)
            docs = ref.limit(limit).get() if limit else ref.get()
        else:
            docs = [ref.get()]

        for doc in docs:
            doc_data = doc.to_dict()
            doc_data["phrase_id"] = doc.id
            record_class = collection_class_map.get(
                collection_name or User.COLLECTION_NAME
            )
            if record_class:
                record_instance = record_class(**doc_data)
                doc_list.append(record_instance)
                logger.info(
                    f"Retrieved from {collection_name or User.COLLECTION_NAME}: {doc.id} => {record_instance}"
                )
            else:
                logger.error(f"No class found for collection name: {collection_name}")
        return doc_list
    except firebase_admin.exceptions.FirebaseError as e:
        logger.error(
            f"Failed to retrieve documents from {collection_name} for {username}. Error: {e}"
        )
        return {}


def get_user_languages(db_client: firestore.Client) -> Dict[str, str]:
    logger.info("Retrieving user languages...")
    user_languages = {}
    allowed_users = get_allowed_users()
    logger.info(f"Allowed users: {allowed_users}")
    for user in allowed_users:
        user_data = get_records(user, db_client)
        user_languages[user] = user_data[0].language
        logger.info(f"User: {user}, Language: {user_data[0].language}")

    return user_languages


def count_records(
    username: str,
    db_client: firestore.Client,
    collection_name: Optional[str] = None,
    where_field: Optional[str] = None,
    where_value: Optional[Any] = None,
) -> int:
    logger.info(f"Counting records for user: {username}, collection: {collection_name}")

    try:
        ref = db_client.collection(User.COLLECTION_NAME).document(username)
        if collection_name:
            ref = ref.collection(collection_name)
            if where_field and where_value is not None:
                logger.info(f"Applying filter: {where_field} == {where_value}")
                ref = ref.where(where_field, "==", where_value)
        count_query = ref.count()
        count_result = count_query.get()
        count = count_result[0][0].value
        logger.info(f"Counted {count} records in {collection_name} for {username}")
        return count
    except firebase_admin.exceptions.FirebaseError as e:
        logger.error(
            f"Failed to count documents in {collection_name} for {username}. Error: {e}"
        )
        return 0


# get random records from the database, incl. where clause
def get_random_record(
    username: str,
    db_client: firestore.Client,
    collection_name: Optional[str] = None,
    where_field: Optional[str] = None,
    where_value: Optional[Any] = None,
) -> BaseModel:
    logger.info(
        f"Getting random record for user: {username}, collection: {collection_name}"
    )

    try:
        ref = db_client.collection(User.COLLECTION_NAME).document(username)
        if collection_name:
            ref = ref.collection(collection_name)
            if where_field and where_value is not None:
                logger.info(f"Applying filter: {where_field} == {where_value}")
                ref = ref.where(where_field, "==", where_value)
        docs = ref.get()
        random_doc = random.choice([doc for doc in docs])
        doc_data = random_doc.to_dict()
        doc_data["phrase_id"] = random_doc.id
        record_class = collection_class_map.get(collection_name or User.COLLECTION_NAME)
        if record_class:
            record_instance = record_class(**doc_data)
            logger.info(
                f"Retrieved random record from {collection_name or User.COLLECTION_NAME}: {random_doc.id} => {record_instance}"
            )
            return record_instance
        else:
            logger.error(f"No class found for collection name: {collection_name}")
            return None
    except firebase_admin.exceptions.FirebaseError as e:
        logger.error(
            f"Failed to retrieve random document from {collection_name} for {username}. Error: {e}"
        )
        return None
