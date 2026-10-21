Формат сообщения: заголовок 8 байт — 4 байта команды ASCII (`!4s`) + 4 байта длины payload (`!I`, big-endian), затем payload. Максимальный размер payload — 10 МБ. Команды: `JOIN` (payload — имя пользователя), `TEXT` (payload — текст), `LIST` (пустой payload), `QUIT` (пустой payload), `ERRO` (payload — описание ошибки), `JOIN` также используется сервером для уведомлений о входе/выходе.

Запуск: `python server.py`, затем `python client.py <username>` в нескольких терминалах.

