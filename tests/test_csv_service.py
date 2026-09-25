import pytest
from app.services.csv_service import parse_participants

def test_parse_valid_csv():
    rows = parse_participants(b"participant_id,name,email\n1,Alice,a@example.com\n", 10)
    assert rows[0]["name"] == "Alice"

def test_parse_missing_column():
    with pytest.raises(ValueError): parse_participants(b"name,email\nAlice,a@example.com\n", 10)

def test_parse_empty():
    with pytest.raises(ValueError): parse_participants(b"participant_id,name,email\n", 10)
