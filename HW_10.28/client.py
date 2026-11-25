import requests

BASE = "http://127.0.0.1:5000"


def show(title, resp):
    print(f"\n=== {title} ===")
    print("status:", resp.status_code)
    try:
        print("json:", resp.json())
    except ValueError:
        print("text:", repr(resp.text))


def main():
    # 0. индекс
    show("GET /", requests.get(f"{BASE}/"))

    # 1. список по умолчанию
    show("GET /notes", requests.get(f"{BASE}/notes"))

    # 2. список с limit/offset
    show("GET /notes?limit=3&offset=2",
         requests.get(f"{BASE}/notes", params={"limit": 3, "offset": 2}))

    # 3. неверный limit -> 400
    show("GET /notes?limit=abc",
         requests.get(f"{BASE}/notes", params={"limit": "abc"}))
    show("GET /notes?limit=0",
         requests.get(f"{BASE}/notes", params={"limit": 0}))

    # 4. сортировка по likes desc
    show("GET /notes?sort=likes&order=desc",
         requests.get(f"{BASE}/notes", params={"sort": "likes", "order": "desc"}))

    # 5. неверная сортировка -> 400
    show("GET /notes?sort=bad",
         requests.get(f"{BASE}/notes", params={"sort": "bad"}))

    # 6. создание заметки -> 201
    new_note = {"author": "ivan", "text": "привет из клиента"}
    r = requests.post(f"{BASE}/notes", json=new_note)
    show("POST /notes (валидная)", r)
    note_id = r.json()["id"] if r.status_code == 201 else None

    # 7. создание без полей -> 400
    show("POST /notes (пусто)", requests.post(f"{BASE}/notes", json={}))

    # 8. создание с пустым author -> 400
    show("POST /notes (пустой author)",
         requests.post(f"{BASE}/notes", json={"author": "  ", "text": "x"}))

    # 9. получить созданную заметку
    if note_id:
        show(f"GET /notes/{note_id}", requests.get(f"{BASE}/notes/{note_id}"))

    # 10. несуществующая заметка -> 404
    show("GET /notes/999999", requests.get(f"{BASE}/notes/999999"))

    # 11. лайки
    if note_id:
        for i in range(3):
            r = requests.post(f"{BASE}/notes/{note_id}/like")
            show(f"POST /notes/{note_id}/like (#{i+1})", r)
    show("POST /notes/999999/like -> 404",
         requests.post(f"{BASE}/notes/999999/like"))

    # 12. обновление
    if note_id:
        show(f"PUT /notes/{note_id}",
             requests.put(f"{BASE}/notes/{note_id}",
                          json={"author": "ivan_updated", "text": "новый текст"}))
    show("PUT /notes/999999 -> 404",
         requests.put(f"{BASE}/notes/999999",
                      json={"author": "x", "text": "y"}))
    if note_id:
        show(f"PUT /notes/{note_id} (без text) -> 400",
             requests.put(f"{BASE}/notes/{note_id}",
                          json={"author": "x"}))

    # 13. статистика по авторам
    show("GET /authors", requests.get(f"{BASE}/authors"))

    # 14. массовое удаление — ошибки
    show("DELETE /notes (без author) -> 400",
         requests.delete(f"{BASE}/notes"))
    show("DELETE /notes?author= (пусто) -> 400",
         requests.delete(f"{BASE}/notes", params={"author": ""}))

    # 15. массовое удаление существующего автора
    show("DELETE /notes?author=ivan_updated",
         requests.delete(f"{BASE}/notes", params={"author": "ivan_updated"}))

    # 16. повторное удаление -> deleted: 0
    show("DELETE /notes?author=ivan_updated (повторно)",
         requests.delete(f"{BASE}/notes", params={"author": "ivan_updated"}))

    # 17. удаление по id
    if note_id:
        # если был удалён массово, вернётся 404 — это тоже полезно увидеть
        show(f"DELETE /notes/{note_id}",
             requests.delete(f"{BASE}/notes/{note_id}"))
    show("DELETE /notes/999999 -> 404",
         requests.delete(f"{BASE}/notes/999999"))

    # 18. неверный метод -> 405
    show("PATCH /notes/1 -> 405",
         requests.patch(f"{BASE}/notes/1", json={}))

    # 19. фильтр по автору
    show("GET /notes?author=alice",
         requests.get(f"{BASE}/notes", params={"author": "alice"}))

    # 20. после всех действий — финальный список
    show("GET /notes (финал)", requests.get(f"{BASE}/notes", params={"limit": 100}))


if __name__ == "__main__":
    main()