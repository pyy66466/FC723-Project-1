from __future__ import annotations
import sqlite3, string, secrets
from typing import Dict, List, Optional

# ---------------- Aircraft-level constants (one airframe, global) ----------------
LETTERS: str = "ABCDEF"                # Seat letters per row
ROWS = range(1, 81)                    # Row numbers 1-80
STORAGE_ROWS = {77, 78}                # Rear storage rows
STORAGE_COLS = {"D", "E", "F"}         # Storage columns

SeatMap = Dict[str, str]               # e.g. {"1A": "F"}, value can be F / S / <booking‑ref>


class SeatBookingSystem:
    """Core booking class.  Status: F (free), S (storage) or 8‑char booking reference."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.seats: SeatMap = {}
        self._init_seats()
        self.conn = sqlite3.connect(db_path)
        self._init_db()
        self._load_existing_bookings()

    # ---------------- schema ----------------
    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS booking(
                ref TEXT,
                passport TEXT,
                first_name TEXT,
                last_name TEXT,
                row INTEGER,
                col TEXT,
                PRIMARY KEY (row, col)      -- one row per seat
            )
            """
        )
        self.conn.commit()

    def _load_existing_bookings(self) -> None:
        """Populate seat map from rows already in the DB (startup sync)."""
        cur = self.conn.cursor()
        for ref, row, col in cur.execute("SELECT ref, row, col FROM booking"):
            code = f"{row}{col}"
            if self.seats.get(code) == "F":   # only update if seat is free
                self.seats[code] = ref

    # ---------------- seat map ----------------
    def _init_seats(self) -> None:
        for r in ROWS:
            for c in LETTERS:
                code = f"{r}{c}"
                self.seats[code] = "S" if r in STORAGE_ROWS and c in STORAGE_COLS else "F"

    # ---------------- reference logic ----------------
    def _new_ref(self) -> str:
        """Return a unique 8‑char reference (A‑Z, 0‑9).

        Algorithm:
        • Uses `secrets.choice` for cryptographic randomness.
        • Checks both in‑memory seat map AND DB for uniqueness.
        """
        alphabet = string.ascii_uppercase + string.digits
        while True:
            ref = "".join(secrets.choice(alphabet) for _ in range(8))
            if ref not in self.seats.values():
                cur = self.conn.cursor()
                if cur.execute("SELECT 1 FROM booking WHERE ref=?", (ref,)).fetchone():
                    continue  # rare collision – try again
                return ref

    # ---------------- validation ----------------------
    def normalise_seat(self, code: str) -> str:
        """Validate input seat code for other functionalities, reject invalid seat codes."""
        code = code.strip().upper()
        if not code or not code[-1].isalpha() or not code[:-1].isdigit():
            raise ValueError("Please input a correct seat code, e.g. 1A or 3F")
        row, letter = int(code[:-1]), code[-1]
        if row not in ROWS or letter not in LETTERS:
            raise ValueError("Sorry! Seat code is outside valid range (1-80, A-F)")
        full = f"{row}{letter}"
        if self.seats[full] == "S":
            raise ValueError(f"Sorry! {full} is storage area and cannot be booked")
        return full

    # ---------------- single-seat ops -----------------
    def seat_status(self, code: str) -> str:
        return self.seats[self.normalise_seat(code)]

    def is_free(self, code: str) -> bool:
        return self.seat_status(code) == "F"

    def book_seat(
        self,
        code: str,
        passport: str,
        first: str,
        last: str,
    ) -> Optional[str]:
        """Return booking reference or None if seat taken."""
        code = self.normalise_seat(code)
        if self.seats[code] != "F":
            return None
        ref = self._new_ref()
        self.seats[code] = ref  # store ref instead of 'R'
        row, col = int(code[:-1]), code[-1]
        self.conn.execute(
            "INSERT INTO booking VALUES (?,?,?,?,?,?)",
            (ref, passport, first, last, row, col),
        )
        self.conn.commit()
        return ref

    def free_seat(self, code: str) -> bool:
        code = self.normalise_seat(code)
        current = self.seats[code]
        if current == "F":
            return False
        # remove DB row
        self.conn.execute("DELETE FROM booking WHERE ref=?", (current,))
        self.conn.commit()
        # reset seat
        self.seats[code] = "F"
        return True

    # ---------------- adjacent-seat ops ---------------
    def find_adjacent(self, n: int) -> Optional[List[str]]:
        """Return *n* consecutive free seats on one side of aisle, else None."""
        if n not in (2, 3):
            raise ValueError("Adjacent booking only supports 2 or 3 passengers.")
        for row in ROWS:
            for side in ("ABC", "DEF"):
                for i in range(len(side) - n + 1):
                    block = [f"{row}{ltr}" for ltr in side[i : i + n]]
                    if all(self.seats[s] == "F" for s in block):
                        return block
        return None

    def book_adjacent(
        self,
        passengers: List[tuple[str, str, str]],
    ) -> Optional[List[tuple[str, str]]]:
        n = len(passengers)
        if n not in (2, 3):
            raise ValueError("Adjacent booking only supports 2 or 3 passengers.")

        block = self.find_adjacent(n)
        if not block:
            return None

        ref = self._new_ref()
        result: list[tuple[str, str]] = []
        for (passport, first, last), seat_code in zip(passengers, block):
            self.seats[seat_code] = ref
            row, col = int(seat_code[:-1]), seat_code[-1]
            self.conn.execute(
                "INSERT INTO booking VALUES (?,?,?,?,?,?)",
                (ref, passport, first, last, row, col),
            )
            result.append((seat_code, ref))
        self.conn.commit()
        return result

    
    # ---------------- reporting -----------------------
    def summary(self) -> Dict[str, int]:
        cnt = {"F": 0, "S": 0, "R": 0}
        for v in self.seats.values():
            cnt["F" if v == "F" else "S" if v == "S" else "R"] += 1
        return {"free": cnt["F"], "reserved": cnt["R"], "storage": cnt["S"]}

    def print_chart(self) -> None:
        print("\nLEGEND  F free | S storage | X aisle | *** = booked ref\n")
        for r in ROWS:
            def cell(ltr: str) -> str:
                val = self.seats[f"{r}{ltr}"]
                return " S " if val == "S" else " F " if val == "F" else "***"
            left = " ".join(cell(l) for l in "ABC")
            right = " ".join(cell(l) for l in "DEF")
            print(f"{r:>2} {left}  X  {right}")
        print()
