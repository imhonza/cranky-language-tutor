import unittest
from unittest.mock import patch, MagicMock

from utils.db import get_records
from utils.db_models import Phrase


class TestDatabaseFunctions(unittest.TestCase):
    @patch("utils.db.collection_class_map", {"phrases": Phrase})
    @patch("utils.db.firestore.Client")
    @patch("utils.db.get_records")
    def test_get_records(self, mock_firestore_client, mock_collection_class_map):
        mock_doc = MagicMock()
        mock_doc.id = "doc1"
        mock_doc.to_dict.return_value = {"text": "hello", "translation": "hola"}
        mock_firestore_client.collection.return_value.document.return_value.collection.return_value.get.return_value = [
            mock_doc
        ]

        db_client = mock_firestore_client
        records = get_records("test_user", db_client, "phrases")
        self.assertIsInstance(records[0], Phrase)
        self.assertEqual(records[0].text, "hello")
        self.assertEqual(records[0].translation, "hola")
