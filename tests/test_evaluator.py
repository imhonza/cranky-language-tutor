import pytest
from unittest.mock import patch

from utils.evaluator import evaluate_task

@pytest.mark.parametrize(
    "task, test_phrase, user_response, expected_outcome, mock_response",
    [
        ("Translate", "I am happy.", "Estoy feliz.", 1, "correct"),
        ("Translate", "I am embarassed.", "Estoy embarazado.", 0, "incorrect"),
        ("Conjugate Verbs", "They are eating.", "Están comiendo.", 1, "correct"),
        ("Conjugate Verbs", "They are eating.", "Comen.", 0, "incorrect"),
        ],
    )

@patch('utils.models.GoogleModel.generate_response')
def test_evaluate_task(mock_generate_response, task, test_phrase, user_response, expected_outcome, mock_response):
    mock_generate_response.return_value = mock_response
    result = evaluate_task(user_response, test_phrase, task)
    assert result["evaluation_outcome"] == expected_outcome
    if expected_outcome == 0:
        assert "incorrect" in result["evaluation_text"].lower()
    else:
        assert "incorrect" not in result["evaluation_text"].lower()
