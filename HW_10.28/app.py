import itertools
import os
import json
from flask import Flask, jsonify, request, abort


app = Flask(__name__)

notes = []
note_ids = itertools.count(1)

STORAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")

_MOCK_AUTHORS = ["alice", "islam", "carl", "dave", "eve"]
_MOCK_TEXTS = [
    "hi!",
    "123",
    "hello",
    "dfsdfsdf",
    "sdfzxvzxc",
    "124234234",
    "work",
    "7473854",
    "lesson",
    "home",
]

for i in range(25):
    notes.append({
        "id": next(note_ids),
        "author": _MOCK_AUTHORS[i % len(_MOCK_AUTHORS)],
        "text": f"{_MOCK_TEXTS[i % len(_MOCK_TEXTS)]} (#{i + 1})",
        "likes": 0,
    })

def _seed_notes():
    return [
        {
            "id": i + 1,
            "author": _MOCK_AUTHORS[i % len(_MOCK_AUTHORS)],
            "text": f"{_MOCK_TEXTS[i % len(_MOCK_TEXTS)]} (#{i + 1})",
            "likes": 0,
        }
        for i in range(25)
    ]

def load_notes():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    data = _seed_notes()
    save_notes(data)
    return data


def save_notes(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


notes = load_notes()
note_ids = itertools.count(max((n["id"] for n in notes), default=0) + 1)



def find_note(note_id):
    return next((n for n in notes if n["id"] == note_id), None)

@app.get("/")
def index():
    return "<h1>Гостевая книга</h1>"


@app.post("/notes")
def create_note():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("author"), str) or not data["author"].strip():
        if not isinstance(data.get("text"), str) or not data["text"].strip():
            return jsonify(error="field 'text' or 'author' (non-empty string) is required"), 400
    note = {"id": next(note_ids), "author": data["author"].strip(), "text": data["text"].strip(), "likes": 0}
    notes.append(note)
    return jsonify(note), 201

@app.get("/notes")
def get_notes(): 
    author = request.args.get("author")
    limit_raw = request.args.get("limit", "10")
    try:
        limit = int(limit_raw)
    except ValueError:
        return jsonify(f"limit должен быть числом, получено '{limit_raw}'"), 400
    if not (1 <= limit <= 100):
        return jsonify("limit должен быть между 1 and 100"), 400

    offset_raw = request.args.get("offset", "0")
    try:
        offset = int(offset_raw)
    except ValueError:
        return jsonify(f"offset должен быть числом, получен:'{offset_raw}'"), 400
    if offset < 0:
        return jsonify("offset должен быть >= 0"), 400

    sort = request.args.get("sort", "id")
    order = request.args.get("order", "asc")

    filtered = notes
    if author is not None:
        filtered = [n for n in filtered if n["author"] == author]

    filtered = sorted(filtered, key=lambda n: n[sort], reverse=(order == "desc"))

    total = len(filtered)
    page = filtered[offset: offset + limit]

    return jsonify({
        "items": page,
        "total": total,
        "limit": limit,
        "offset": offset,
    })

@app.get("/notes/<int:note_id>")
def get_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    return jsonify(note)

@app.put("/notes/<int:note_id>")
def put_note(note_id): 
    data = request.get_json(silent=True)
    note = find_note(note_id)
    if note is None:
            abort(404)
    if  not isinstance(data, dict) or not isinstance(data["author"], str) or not data["author"].strip(): 
        if not isinstance(data.get("text"), str) or not data["text"].strip():
            return jsonify(error="field 'text' or 'author' (non-empty string) is required"), 400
    note["author"] = data["author"].strip()
    note["text"] = data["text"].strip()
    response_text = f"Товар с id {note_id} успешно обновлен."
    return {
        "message": response_text,
        "updated_fields": {
            "author": data["author"],
            "text": data["text"]
        }
    }, 200

@app.delete("/notes/<int:note_id>")
def delete_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    notes.remove(note)
    return "", 204

@app.post("/notes/<int:note_id>/like")
def like_note(note_id):
    note = find_note(note_id)
    if note is None:
        abort(404)
    note["likes"] = note.get("likes", 0) + 1
    save_notes(notes)
    return jsonify(note), 200

@app.get("/authors")
def get_authors():
    stats = {}
    for n in notes:
        a = n["author"]
        if a not in stats:
            stats[a] = {"author": a, "notes": 0, "likes": 0}
        stats[a]["notes"] += 1
        stats[a]["likes"] += n.get("likes", 0)

    result = sorted(stats.values(), key=lambda x: x["author"])
    return jsonify(result)

@app.delete("/notes")
def delete_notes_by_author():
    author = request.args.get("author")
    if author is None or not author.strip():
        return jsonify(error="query parameter 'author' is required and must be non-empty"), 400
    author = author.strip()

    to_delete = [n for n in notes if n["author"] == author]
    deleted = len(to_delete)
    if deleted:
        notes = [n for n in notes if n["author"] != author]
        save_notes(notes)

    return jsonify(deleted=deleted), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify(error="not found"), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify(error="method not allowed"), 405

if __name__ == "__main__":
    app.run(debug=True)