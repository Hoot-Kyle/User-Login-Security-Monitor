import random
import sqlite3
import time
from pathlib import Path

from faker import Faker

# CONSTANTS/INITIALIZATION:
DB_PATH = Path(__file__).parent / "logins.db"
EMPLOYEE_COUNT = 18

SUSPICIOUS_COUNTRIES = ("Russia", "China", "Iran", "North Korea")
NORMAL_COUNTRIES = ("United States", "United Kingdom", "Canada", "Germany", "Australia", "France", "Japan")
KNOWN_DEVICES = ("Windows-Laptop", "MacBook-Pro", "iPhone-14", "Android-Pixel", "Surface-Pro")

fake = Faker()


def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upn TEXT NOT NULL,
            country TEXT NOT NULL,
            device TEXT NOT NULL,
            successful INTEGER NOT NULL,
            login_time TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def build_employee_pool():
    return [fake.user_name() + "@company.com" for _ in range(EMPLOYEE_COUNT)]


def random_event(employees):
    upn = random.choice(employees)

    if random.random() < 0.08:
        country = random.choice(SUSPICIOUS_COUNTRIES)
    else:
        country = random.choice(NORMAL_COUNTRIES)

    if random.random() < 0.05:
        device = f"UNKNOWN-{fake.hexify(text='^^^^').upper()}"
    else:
        device = random.choice(KNOWN_DEVICES)

    successful = int(random.random() > 0.12)

    if random.random() < 0.15:
        hour = random.choice(list(range(0, 7)) + list(range(19, 24)))
    else:
        hour = random.randint(7, 18)
    login_time = f"{hour:02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"

    return upn, country, device, successful, login_time


def main():
    conn = init_db()
    employees = build_employee_pool()
    print(f"Streaming simulated logins into {DB_PATH} (Ctrl+C to stop)")

    try:
        while True:
            event = random_event(employees)
            conn.execute(
                "INSERT INTO logins (upn, country, device, successful, login_time) VALUES (?, ?, ?, ?, ?)",
                event,
            )
            conn.commit()
            print("Inserted:", event)
            time.sleep(random.uniform(1, 3))
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
