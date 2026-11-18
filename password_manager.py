"""Учебный CLI-менеджер паролей для домашнего задания."""

import os
import sqlite3
import sys
import warnings
from contextlib import closing
from getpass import GetPassWarning, getpass
from hashlib import sha256
from hmac import compare_digest
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from password_gen import DEFAULT_SPECIALS, MAX_LENGTH, PasswordGenerator


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "password.db"
KEY_PATH = PROJECT_DIR / ".key"


class DatabaseManager:
    def __init__(self, path):
        self.connection = sqlite3.connect(path)
        try:
            self.init_database()
        except Exception:
            self.connection.close()
            raise

    def init_database(self):
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS master_password (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS passwords (
                service_key TEXT PRIMARY KEY,
                service TEXT NOT NULL,
                login TEXT NOT NULL,
                encrypted_password BLOB NOT NULL
            );
        """)

    def set_master_password(self, password):
        with self.connection:
            result = self.connection.execute(
                "INSERT OR IGNORE INTO master_password VALUES (1, ?)",
                (master_hash(password),),
            )
        return result.rowcount == 1

    def get_master_password(self):
        row = self.connection.execute("SELECT password_hash FROM master_password WHERE id = 1").fetchone()
        return row[0] if row else None

    def add_password(self, service, login, encrypted_password):
        service = service.strip()
        login = login.strip()
        if not service or not login:
            raise ValueError("Введи название и логин.")
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO passwords VALUES (?, ?, ?, ?)",
                    (service.casefold(), service, login, encrypted_password),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Запись с таким названием уже есть.") from exc

    def get_password(self, service):
        return self.connection.execute(
            "SELECT service, login, encrypted_password FROM passwords WHERE service_key = ?",
            (service.strip().casefold(),),
        ).fetchone()

    def list_passwords(self):
        return self.connection.execute("SELECT service, login FROM passwords ORDER BY service_key").fetchall()

    def delete_password(self, service):
        with self.connection:
            result = self.connection.execute(
                "DELETE FROM passwords WHERE service_key = ?", (service.strip().casefold(),),
            )
        return result.rowcount == 1

    def open_encryption(self, key_path):
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            has_data = self.connection.execute("SELECT EXISTS(SELECT 1 FROM passwords)").fetchone()[0]
            return EncryptionManager(key_path, allow_create=not has_data)

    def close(self):
        self.connection.close()


class EncryptionManager:
    def __init__(self, path, allow_create):
        try:
            key = path.read_bytes()
        except FileNotFoundError:
            if not allow_create:
                raise ValueError("Файл .key отсутствует. Верни исходный ключ, чтобы прочитать записи.") from None
            key = Fernet.generate_key()
            try:
                descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                key = path.read_bytes()
            else:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(key)
        try:
            self.fernet = Fernet(key)
        except (ValueError, TypeError) as exc:
            raise ValueError("Файл .key повреждён. Для расшифровки нужен исходный ключ.") from exc

    def encrypt(self, password):
        return self.fernet.encrypt(password.encode("utf-8"))

    def decrypt(self, token):
        try:
            return self.fernet.decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Не удалось расшифровать запись. Проверь, что сохранён исходный файл .key.") from exc


def master_hash(password):
    return sha256(password.encode("utf-8")).hexdigest()


def read_hidden(prompt):
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        return getpass(prompt)


def setup_master_password(database):
    while True:
        first = read_hidden("Придумай мастер-пароль: ")
        if not first:
            print("Укажи непустой мастер-пароль.")
            continue
        if first != read_hidden("Повтори мастер-пароль: "):
            print("Введённые значения различаются. Попробуй ещё раз.")
            continue
        return database.set_master_password(first)


def authenticate(database):
    saved_hash = database.get_master_password()
    if saved_hash is None:
        if setup_master_password(database):
            return True
        saved_hash = database.get_master_password()
    for _ in range(3):
        if compare_digest(saved_hash, master_hash(read_hidden("Мастер-пароль: "))):
            return True
        print("Неверный мастер-пароль.")
    return False


def confirm(question, default=True):
    hint = "Д/н" if default else "д/Н"
    while True:
        response = input(f"{question} [{hint}]: ").strip().casefold()
        if not response:
            return default
        if response in ("д", "да", "y", "yes"):
            return True
        if response in ("н", "нет", "n", "no"):
            return False
        print("Введи д или н.")


def generate_password_interactive():
    while True:
        text = input(f"Длина пароля от 1 до {MAX_LENGTH} [16]: ").strip()
        try:
            length = int(text or 16)
        except ValueError:
            print("Введи целое число.")
            continue
        if 1 <= length <= MAX_LENGTH:
            break
        print(f"Допустимая длина от 1 до {MAX_LENGTH} символов.")

    uppercase = confirm("Заглавные буквы")
    lowercase = confirm("Строчные буквы")
    digits = confirm("Цифры")
    specials = confirm("Спецсимволы")
    special_chars = DEFAULT_SPECIALS
    if specials:
        special_chars = input(f"Разрешённые спецсимволы [{DEFAULT_SPECIALS}]: ") or DEFAULT_SPECIALS
    exclude = confirm("Исключить похожие символы 0, O, 1, I и l")
    return PasswordGenerator(
        length=length,
        uppercase=uppercase,
        lowercase=lowercase,
        digits=digits,
        specials=specials,
        exclude_ambiguous=exclude,
        special_chars=special_chars,
    ).generate()[0]


def add_password(database, encryption):
    service = input("Сервис: ").strip()
    login = input("Логин: ").strip()
    if not service or not login:
        raise ValueError("Введи название и логин.")
    autogenerated = confirm("Сгенерировать пароль")
    password = generate_password_interactive() if autogenerated else read_hidden("Пароль записи: ")
    if not password:
        raise ValueError("Введи непустой пароль.")
    database.add_password(service, login, encryption.encrypt(password))
    print("Запись сохранена.")


def show_password(database, encryption):
    entry = database.get_password(input("Название сервиса: "))
    if entry is None:
        print("Запись не найдена.")
        return
    service, login, token = entry
    print(f"Сервис: {service}\nЛогин: {login}\nПароль: {encryption.decrypt(token)}")


def show_list(database):
    rows = database.list_passwords()
    if not rows:
        print("Пока нет сохранённых записей.")
        return
    headings = ("Сервис", "Логин")
    service_width = max(len(headings[0]), *(len(row[0]) for row in rows))
    login_width = max(len(headings[1]), *(len(row[1]) for row in rows))
    divider = f"+-{'-' * service_width}-+-{'-' * login_width}-+"
    print(divider)
    print(f"| {headings[0]:<{service_width}} | {headings[1]:<{login_width}} |")
    print(divider)
    for service, login in rows:
        print(f"| {service:<{service_width}} | {login:<{login_width}} |")
    print(divider)


def delete_password(database):
    service = input("Название сервиса: ").strip()
    if database.get_password(service) is None:
        print("Запись не найдена.")
        return
    if confirm(f"Удалить «{service}»", default=False):
        if database.delete_password(service):
            print("Запись удалена.")
        else:
            print("Запись не найдена.")


def show_menu(database, encryption):
    def new_password():
        print(f"Новый пароль: {generate_password_interactive()}")

    commands = {
        "new": new_password,
        "add": lambda: add_password(database, encryption),
        "list": lambda: show_list(database),
        "get": lambda: show_password(database, encryption),
        "delete": lambda: delete_password(database),
    }
    while True:
        print("\nnew — создать  add — сохранить  list — таблица\n"
              "get — показать пароль  delete — удалить  exit — выйти")
        command = input("Команда: ").strip().casefold()
        if command == "exit":
            return
        if command not in commands:
            print("Выбери команду из меню.")
            continue
        try:
            commands[command]()
        except ValueError as exc:
            print(exc)


def main(database_path=DATABASE_PATH, key_path=KEY_PATH):
    try:
        with closing(DatabaseManager(database_path)) as database:
            if not authenticate(database):
                return 1
            encryption = database.open_encryption(key_path)
            print("\nМенеджер паролей")
            show_menu(database, encryption)
    except (EOFError, KeyboardInterrupt):
        print("\nСеанс завершён.")
    except GetPassWarning:
        print("Терминал не поддерживает скрытый ввод. Запусти программу в терминале VS Code или PowerShell.", file=sys.stderr)
        return 1
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
