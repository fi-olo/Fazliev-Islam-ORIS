
from flask import Flask, render_template, request, redirect, url_for, abort, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key-change-this"
app.config["SESSION_TYPE"] = "filesystem"

Session(app)


def connect_db():
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect_db()

    try:
        conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password  TEXT NOT NULL)
                """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holder TEXT NOT NULL,
                card TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL DEFAULT 0 CHECK (balance >= 0),
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) 
                    REFERENCES users (id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                comment TEXT NOT NULL,
                FOREIGN KEY (account_id)
                    REFERENCES accounts (id)
                    ON DELETE CASCADE
            )
        """)

        conn.commit()

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


def find_account(account_id):
    conn = connect_db()

    try:
        item = conn.execute(
            "SELECT * FROM accounts WHERE id = ?",
            (account_id,)
        ).fetchone()

        return item

    finally:
        conn.close()


def all_account():
    conn = connect_db()

    try:
        items = conn.execute(
            "SELECT * FROM accounts"
        ).fetchall()

        return items

    finally:
        conn.close()


def append_account(holder, card, balance):
    conn = connect_db()

    try:
        conn.execute(
            """
            INSERT INTO accounts (holder, card, balance)
            VALUES (?, ?, ?)
            """,
            (holder, card, balance)
        )

        conn.commit()

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


def update_account(account_id, holder, card, balance):
    conn = connect_db()

    try:
        conn.execute(
            """
            UPDATE accounts
            SET holder = ?, card = ?, balance = ?
            WHERE id = ?
            """,
            (holder, card, balance, account_id)
        )

        conn.commit()

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


def delete_account(account_id):
    conn = connect_db()

    try:
        conn.execute(
            "DELETE FROM accounts WHERE id = ?",
            (account_id,)
        )

        conn.commit()

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


def get_account_history(account_id):
    conn = connect_db()

    try:
        items = conn.execute(
            """
            SELECT *
            FROM history
            WHERE account_id = ?
            ORDER BY id DESC
            """,
            (account_id,)
        ).fetchall()

        return items

    finally:
        conn.close()


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

def register_users(username, email, password):
    conn = connect_db()
    try:
        hash_password = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hash_password))

        conn.commit()

    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def find_user(email):
    conn = connect_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return user
    finally:
        conn.close()

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        errors = []

        if not username:
            errors.append("Введите имя")

        if not email:
            errors.append("Введите email")

        if len(password) < 6:
            errors.append("Пароль должен содержать минимум 6 символов")

        if errors:
            return render_template("register.html", errors=errors, username=username, email=email)

        try:
            register_users(username, email, password)
        except sqlite3.IntegrityError:
            errors.append("Пользователь с таким email уже существует")
            return render_template("register.html",
                                   errors=errors, username=username, email=email)
        user = find_user(email)

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return render_template("index.html")

    return render_template("register.html")

@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "")

    result = all_account()

    if query:
        q_lower = query.lower()

        result = [
            a for a in result
            if q_lower in a["holder"].lower()
            or q_lower in a["card"].lower()
        ]

    if sort_by == "balance":
        result = sorted(result, key=lambda a: a["balance"])

    elif sort_by == "balance_desc":
        result = sorted(
            result,
            key=lambda a: a["balance"],
            reverse=True
        )

    elif sort_by == "holder":
        result = sorted(
            result,
            key=lambda a: a["holder"].lower()
        )

    return render_template(
        "index.html",
        accounts=result,
        query=query,
        sort_by=sort_by
    )


@app.route("/accounts/<int:account_id>")
def detail(account_id):
    account = find_account(account_id)

    if account is None:
        abort(404)

    account = dict(account)
    account["history"] = get_account_history(account_id)

    return render_template(
        "detail.html",
        account=account
    )


@app.route("/accounts/add", methods=["GET", "POST"])
def add_account():
    if request.method == "POST":
        holder = request.form.get("holder", "").strip()
        card = request.form.get("card", "").strip()
        balance_raw = request.form.get("balance", "").strip()

        errors, balance = validate_account_form(
            holder,
            card,
            balance_raw
        )

        if errors:
            return render_template(
                "add.html",
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw
            )

        try:
            append_account(holder, card, balance)

        except sqlite3.IntegrityError:
            errors.append("Такой номер карты уже существует")

            return render_template(
                "add.html",
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw
            )

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

        errors, balance = validate_account_form(
            holder,
            card,
            balance_raw
        )

        if errors:
            return render_template(
                "edit.html",
                account=account,
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw
            )

        try:
            update_account(
                account["id"],
                holder,
                card,
                balance
            )

        except sqlite3.IntegrityError:
            errors.append("Такой номер карты уже существует")

            return render_template(
                "edit.html",
                account=account,
                errors=errors,
                holder=holder,
                card=card,
                balance=balance_raw
            )

        return redirect(
            url_for("detail", account_id=account["id"])
        )

    return render_template(
        "edit.html",
        account=account,
        holder=account["holder"],
        card=account["card"],
        balance=account["balance"]
    )


@app.route("/accounts/<int:account_id>/delete", methods=["POST"])
def remove_account(account_id):
    account = find_account(account_id)

    if account is None:
        abort(404)

    delete_account(account_id)

    return redirect(url_for("index"))


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    accounts = all_account()

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
                accounts=all_account(),
                errors=errors,
                from_id=from_id,
                to_id=to_id,
                amount=amount_raw
            )

        conn = connect_db()

        try:
            sender_db = conn.execute(
                "SELECT * FROM accounts WHERE id = ?",
                (from_id,)
            ).fetchone()

            receiver_db = conn.execute(
                "SELECT * FROM accounts WHERE id = ?",
                (to_id,)
            ).fetchone()

            if sender_db is None or receiver_db is None:
                abort(404)

            if sender_db["balance"] < amount:
                errors.append(
                    "Недостаточно средств на счёте отправителя"
                )

                return render_template(
                    "transfer.html",
                    accounts=all_account(),
                    errors=errors,
                    from_id=from_id,
                    to_id=to_id,
                    amount=amount_raw
                )

            conn.execute(
                """
                UPDATE accounts
                SET balance = balance - ?
                WHERE id = ?
                """,
                (amount, from_id)
            )

            conn.execute(
                """
                UPDATE accounts
                SET balance = balance + ?
                WHERE id = ?
                """,
                (amount, to_id)
            )

            conn.execute(
                """
                INSERT INTO history
                (account_id, type, amount, comment)
                VALUES (?, ?, ?, ?)
                """,
                (
                    from_id,
                    "Перевод",
                    -amount,
                    f"Перевод для {receiver_db['holder']}"
                )
            )

            conn.execute(
                """
                INSERT INTO history
                (account_id, type, amount, comment)
                VALUES (?, ?, ?, ?)
                """,
                (
                    to_id,
                    "Пополнение",
                    amount,
                    f"Перевод от {sender_db['holder']}"
                )
            )

            conn.commit()

        except sqlite3.Error:
            conn.rollback()
            errors.append("Ошибка базы данных при переводе")

            return render_template(
                "transfer.html",
                accounts=all_account(),
                errors=errors,
                from_id=from_id,
                to_id=to_id,
                amount=amount_raw
            )

        finally:
            conn.close()

        return redirect(
            url_for("detail", account_id=from_id)
        )

    return render_template(
        "transfer.html",
        accounts=accounts
    )


@app.route("/stats")
def stats():
    accounts = all_account()

    total = sum(a["balance"] for a in accounts)
    count = len(accounts)
    avg = total / count if count else 0

    top = sorted(
        accounts,
        key=lambda a: a["balance"],
        reverse=True
    )[:3]

    max_acc = max(
        accounts,
        key=lambda a: a["balance"],
        default=None
    )

    min_acc = min(
        accounts,
        key=lambda a: a["balance"],
        default=None
    )

    return render_template(
        "stats.html",
        count=count,
        total=total,
        avg=avg,
        top=top,
        max_acc=max_acc,
        min_acc=min_acc
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


init_db()


if __name__ == "__main__":
    app.run(debug=True)
