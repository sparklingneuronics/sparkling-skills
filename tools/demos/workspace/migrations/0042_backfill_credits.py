"""Backfill loyalty credits for legacy accounts (one-off migration).

Adds each legacy account's historical signup bonus to its live balance, then
marks the account as backfilled so we never credit it twice.
"""
import time

from db import connect

RETRIES = 3


def backfill(conn):
    accounts = conn.execute(
        "SELECT id, signup_bonus FROM accounts WHERE credits_backfilled = 0"
    ).fetchall()

    for acct in accounts:
        # credit the historical signup bonus onto the current balance
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (acct["signup_bonus"], acct["id"]),
        )
        conn.commit()  # commit each account so a long backfill can resume if interrupted

    # everyone's credited — flag them so we never run it twice
    conn.execute("UPDATE accounts SET credits_backfilled = 1 WHERE credits_backfilled = 0")
    conn.commit()


def run():
    conn = connect()
    for attempt in range(1, RETRIES + 1):
        try:
            backfill(conn)
            print("backfill complete")
            return
        except Exception as exc:  # lock timeout, dropped connection, etc.
            print(f"attempt {attempt} failed: {exc!r} - retrying")
            time.sleep(2)
    raise SystemExit("backfill failed after retries")


if __name__ == "__main__":
    run()
