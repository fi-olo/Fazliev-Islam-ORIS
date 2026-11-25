from flask import Flask, render_template, request, redirect, url_for

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


@app.route("/")
def index():
    return render_template("index.html", accounts=accounts)


@app.route("/accounts/<int:account_id>")
def detail(account_id):
    account = None
    for item in accounts:
        if item["id"] == account_id:
            account = item
            break

    if account is None:
        return "Account not found", 404

    return render_template("detail.html", account=account)


@app.route("/accounts/add", methods=["GET", "POST"])
def add_account():
    if request.method == "POST":
        holder = request.form.get("holder", "").strip()
        card = request.form.get("card", "").strip()
        balance_raw = request.form.get("balance", "").strip()

        errors = []

        if not holder:
            errors.append("Имя владельца обязательно")

        if not card:
            errors.append("Номер карты обязателен")

        balance = 0.0
        if balance_raw:
            try:
                balance = float(balance_raw)
                if balance < 0:
                    errors.append("Баланс не может быть отрицательным")
            except ValueError:
                errors.append("Баланс должен быть числом")

        if errors:
            return render_template(
                "add.html",
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw,
            )

        new_account = {
            "id": len(accounts) + 1,
            "holder": holder,
            "card": card,
            "balance": balance,
            "history": [],
        }

        accounts.append(new_account)
        return redirect(url_for("index"))

    return render_template("add.html")

@app.route('/tranfer', methods = ["GET", "POST"])
def transfer(): 
    if request.method == "POST": 
        from_id = request.form.get("from_id", "").strip()
        to_id = request.form.get("to_id", "").strip()
        amount = request.form.get("amount", )

        errors = []

        sender = None
        receiver = None

        if not from_id:
            errors.append("Счёт отправителя обязателен")
        else:
            try:
                from_id = int(from_id)
            except ValueError:
                errors.append("Некорректный счёт отправителя")
                from_id = None

            if from_id is not None:
                for item in accounts:
                    if item["id"] == from_id:
                        sender = item
                        break
                if sender is None:
                    errors.append("Счёт отправителя не найден")

        if not to_id:
            errors.append("Счёт получателя обязателен")
        else:
            try:
                to_id = int(to_id)
            except ValueError:
                errors.append("Некорректный счёт отправителя")
                to_id = None

            if to_id is not None:
                for item in accounts:
                    if item["id"] == to_id:
                        receiver = item
                        break
                if receiver is None:
                    errors.append("Счёт отправителя не найден")


        if not amount:
            errors.append("Сумма обязательна")
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    errors.append("Сумма должна быть больше нуля")
            except ValueError:
                errors.append("Сумма должна быть числом")

        if sender is not None and amount > 0 and sender["balance"] < amount:
            errors.append("Недостаточно средств на счёте отправителя")


        if errors:
            return render_template(
                "transfer.html",
                accounts=accounts,
                errors=errors,
                from_id=from_id,
                to_id=to_id,
                amount=amount,
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
        
if __name__ == "__main__": 
    app.run(debug=True)