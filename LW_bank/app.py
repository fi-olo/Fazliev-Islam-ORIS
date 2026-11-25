from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

accounts = [
    {
        "id": 1,
        "holder": "Фазлиев Ислам",
        "card": "4276 1234 5678 9012",
        "balance": 15000.0,
        "history": [
            {"type": "Пополнение", "amount": 5000.0, "comment": "Зарплата"},
            {"type": "Перевод", "amount": -1200.0, "comment": "Оплата интернета"},
        ],
    },
    {
        "id": 2,
        "holder": "Ива Иванов",
        "card": "4276 9876 5432 1098",
        "balance": 8700.5,
        "history": [
            {"type": "Пополнение", "amount": 10000.0, "comment": "Перевод от клиента"},
            {"type": "Перевод", "amount": -3000.0, "comment": "Аренда"},
        ],
    },
    {
        "id": 3,
        "holder": "Пётр Первый",
        "card": "4276 1111 2222 3333",
        "balance": 320.0,
        "history": [
            {"type": "Перевод", "amount": -150.0, "comment": "Кофе"},
        ],
    },
]


def find_account(account_id):
    for item in accounts:
        if item["id"] == account_id:
            return item
    return None


def validate_account_form(holder, card, balance_raw):
    errors = []
    balance = 0.0

    if not holder:
        errors.append("Имя владельца обязательно")

    if not card:
        errors.append("Номер карты обязателен")

    if balance_raw:
        try:
            balance = float(balance_raw)
            if balance < 0:
                errors.append("Баланс не может быть отрицательным")
        except ValueError:
            errors.append("Баланс должен быть числом")
            balance = 0.0
    else:
        errors.append("Баланс обязателен")

    return errors, balance


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "")

    result = accounts

    if query:
        q_lower = query.lower()
        result = [
            a for a in result
            if q_lower in a["holder"].lower() or q_lower in a["card"].lower()
        ]

    if sort_by == "balance":
        result = sorted(result, key=lambda a: a["balance"])
    elif sort_by == "balance_desc":
        result = sorted(result, key=lambda a: a["balance"], reverse=True)
    elif sort_by == "holder":
        result = sorted(result, key=lambda a: a["holder"].lower())

    return render_template(
        "index.html",
        accounts=result,
        query=query,
        sort_by=sort_by,
    )


@app.route("/accounts/<int:account_id>")
def detail(account_id):
    account = find_account(account_id)
    if account is None:
        abort(404)
    return render_template("detail.html", account=account)


@app.route("/accounts/add", methods=["GET", "POST"])
def add_account():
    if request.method == "POST":
        holder = request.form.get("holder", "").strip()
        card = request.form.get("card", "").strip()
        balance_raw = request.form.get("balance", "").strip()

        errors, balance = validate_account_form(holder, card, balance_raw)

        if errors:
            return render_template(
                "add.html",
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw,
            )

        new_id = max((a["id"] for a in accounts), default=0) + 1
        accounts.append({
            "id": new_id,
            "holder": holder,
            "card": card,
            "balance": balance,
            "history": [],
        })
        return redirect(url_for("index"))

    return render_template("add.html")


@app.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
def edit_account(account_id):
    account = find_account(account_id)
    if account is None:
        abort(404)

    if request.method == "POST":
        holder = request.form.get("holder", "").strip()
        card = request.form.get("card", "").strip()
        balance_raw = request.form.get("balance", "").strip()

        errors, balance = validate_account_form(holder, card, balance_raw)

        if errors:
            return render_template(
                "edit.html",
                account=account,
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw,
            )

        account["holder"] = holder
        account["card"] = card
        account["balance"] = balance
        return redirect(url_for("detail", account_id=account["id"]))

    return render_template(
        "edit.html",
        account=account,
        holder=account["holder"],
        card=account["card"],
        balance=account["balance"],
    )


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "POST":
        from_id = request.form.get("from_id", "").strip()
        to_id = request.form.get("to_id", "").strip()
        amount_raw = request.form.get("amount", "").strip()

        errors = []
        sender = receiver = None
        amount = 0.0

        if not from_id:
            errors.append("Счёт отправителя обязателен")
        else:
            try:
                from_id = int(from_id)
                sender = find_account(from_id)
                if sender is None:
                    errors.append("Счёт отправителя не найден")
            except ValueError:
                errors.append("Некорректный счёт отправителя")
                from_id = None

        if not to_id:
            errors.append("Счёт получателя обязателен")
        else:
            try:
                to_id = int(to_id)
                receiver = find_account(to_id)
                if receiver is None:
                    errors.append("Счёт получателя не найден")
            except ValueError:
                errors.append("Некорректный счёт получателя")
                to_id = None

        if sender and receiver and sender["id"] == receiver["id"]:
            errors.append("Нельзя перевести на тот же счёт")

        if not amount_raw:
            errors.append("Сумма обязательна")
        else:
            try:
                amount = float(amount_raw)
                if amount <= 0:
                    errors.append("Сумма должна быть больше нуля")
            except ValueError:
                errors.append("Сумма должна быть числом")
                amount = 0.0

        if sender and amount > 0 and sender["balance"] < amount:
            errors.append("Недостаточно средств на счёте отправителя")

        if errors:
            return render_template(
                "transfer.html",
                accounts=accounts,
                errors=errors,
                from_id=from_id,
                to_id=to_id,
                amount=amount_raw,
            )

        sender["balance"] -= amount
        receiver["balance"] += amount
        sender["history"].append({
            "type": "Перевод",
            "amount": -amount,
            "comment": f"Перевод для {receiver['holder']}",
        })
        receiver["history"].append({
            "type": "Пополнение",
            "amount": amount,
            "comment": f"Перевод от {sender['holder']}",
        })
        return redirect(url_for("detail", account_id=sender["id"]))

    return render_template("transfer.html", accounts=accounts)


@app.route("/stats")
def stats():
    total = sum(a["balance"] for a in accounts)
    count = len(accounts)
    avg = total / count if count else 0
    top = sorted(accounts, key=lambda a: a["balance"], reverse=True)[:3]

    max_acc = max(accounts, key=lambda a: a["balance"], default=None)
    min_acc = min(accounts, key=lambda a: a["balance"], default=None)

    return render_template(
        "stats.html",
        count=count,
        total=total,
        avg=avg,
        top=top,
        max_acc=max_acc,
        min_acc=min_acc,
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)