import csv, io
REQUIRED = {"participant_id", "name", "email"}

def parse_participants(data: bytes, max_rows: int):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("Participant CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not REQUIRED.issubset({h.strip() for h in reader.fieldnames}):
        raise ValueError("CSV must contain participant_id,name,email columns")
    rows = []
    for idx, row in enumerate(reader, start=2):
        if len(rows) >= max_rows:
            raise ValueError(f"Batch exceeds maximum of {max_rows} participants")
        clean = {str(k).strip(): (v or "").strip() for k, v in row.items()}
        if not clean.get("participant_id") or not clean.get("name") or not clean.get("email"):
            raise ValueError(f"Missing required value at CSV row {idx}")
        rows.append(clean)
    if not rows:
        raise ValueError("CSV contains no participants")
    return rows
