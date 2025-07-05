from __future__ import annotations
import os, datetime, sqlite3, string, secrets
from pathlib import Path
from typing import Dict, List, Optional

# ---------------- Aircraft-level constants (one airframe, global) ----------------
LETTERS: str = "ABCDEF"                # Seat letters per row
ROWS = range(1, 81)                    # Row numbers 1-80
STORAGE_ROWS = {77, 78}                # Rear storage rows
STORAGE_COLS = {"D", "E", "F"}         # Storage columns

SeatMap = Dict[str, str]               # e.g. {"1A": "F"}, value can be F / S / <booking‑ref>


class SeatBookingSystem:
    """Core booking class.  Status: F (free), S (storage) or 8‑char booking reference."""

    def __init__(self, db_path: str | os.PathLike | None = "booking.db") -> None:
        self.seats: SeatMap = {}
        self._init_seats()
        self.db_path = db_path
        self.conn = self._open_or_create_db(db_path)
        self._assure_schema()
        self._load_existing_bookings()

    # ---------------- seat map initialisation ----------------
    def _init_seats(self) -> None:
        for r in ROWS:
            for c in LETTERS:
                code = f"{r}{c}"
                self.seats[code] = "S" if r in STORAGE_ROWS and c in STORAGE_COLS else "F"

    # ---------------- db ----------------
    def _open_or_create_db(self, db_path):
        """
        Open or create db, handles E1, E2, E3:
        - E1: db_path is None or empty
        - E2: Folder in db_path does not exist
        - E3: File exists but is not SQLite (binary or text file)
        
        """
        if not db_path:
            return sqlite3.connect(":memory:")

        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)  # E2

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA schema_version")  # Force SQLite to parse DB file
            return conn
        except sqlite3.DatabaseError:
            ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            corrupt = db_path.with_suffix(f".corrupt-{ts}.db")
            db_path.rename(corrupt)
            print(f"[WARN] Corrupt DB renamed to {corrupt}")
            return sqlite3.connect(db_path)  # fresh empty file
        
    def _create_booking_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE booking(
                ref TEXT,                 -- shared reference
                passport TEXT,
                first_name TEXT,
                last_name TEXT,
                row INTEGER,
                col TEXT,
                PRIMARY KEY (row, col)    -- one row PER SEAT
            )
            """
        )
        self.conn.commit()

    def _assure_schema(self):
        """
        Assure db schema, handles E4, E5:
        - E4: File is SQLite but contains no booking table
        - E5: booking table exists but has missing / extra columns
        """
        cur = self.conn.cursor()
        # Does booking table exist?
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='booking'"
        )
        if not cur.fetchone():  # E4
            self._create_booking_table()
            return

        # Verify required columns
        cur.execute("PRAGMA table_info(booking)")
        existing_cols = {row[1] for row in cur.fetchall()}
        required = {
            "ref",
            "passport",
            "first_name",
            "last_name",
            "row",
            "col",
        }
        missing = required - existing_cols
        extra = existing_cols - required
        if missing:
            # attempt simple ALTER TABLE for each missing column
            for col in missing:
                if col in {"row"}:
                    cur.execute("ALTER TABLE booking ADD COLUMN row INTEGER")
                elif col in {"col"}:
                    cur.execute("ALTER TABLE booking ADD COLUMN col TEXT")
                else:
                    cur.execute(f"ALTER TABLE booking ADD COLUMN {col} TEXT")
            self.conn.commit()
        if extra:
            print(
                "[WARN] booking table has unexpected columns – "
                "program continues but they will be ignored: ",
                extra,
            )
    
    def _load_existing_bookings(self) -> None:
        """
        Populate seat map from rows already in the DB (startup sync), handles E6:
        - E6: Booking table has data but seat map still initialises with 'F' for those seats
        """
        cur = self.conn.cursor()
        for ref, row, col in cur.execute("SELECT ref, row, col FROM booking"):
            code = f"{row}{col}"
            if self.seats.get(code) == "F":   # only update if seat is free
                self.seats[code] = ref

    # ---------------- reference logic ----------------
    def _new_ref(self) -> str:
        """Return a unique 8‑char reference (A‑Z, 0‑9).

        Algorithm:
        - Uses `secrets.choice` for cryptographic randomness.
        - Checks both in‑memory seat map AND DB for uniqueness.
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
        self.seats[code] = ref
        return ref

    def free_seat(self, code: str) -> bool:
        code = self.normalise_seat(code)
        current = self.seats[code]
        if current == "F":
            return False
        row, col = int(code[:-1]), code[-1]
        self.conn.execute(
            "DELETE FROM booking WHERE row=? AND col=?", (row, col)
        )
        self.conn.commit()
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

        result: list[tuple[str, str]] = []
        for (passport, first, last), seat_code in zip(passengers, block):
            ref = self._new_ref()
            row, col = int(seat_code[:-1]), seat_code[-1]
            self.conn.execute(
                "INSERT INTO booking VALUES (?,?,?,?,?,?)",
                (ref, passport, first, last, row, col),
            )
            self.seats[seat_code] = ref
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
        print("\nLEGEND  F = free | *** = booked | S = storage | X = aisle\n")
        print("      A   B   C    X    D   E   F")  # Column headers, padded to match seats

        for r in ROWS:
            def cell(ltr: str) -> str:
                val = self.seats[f"{r}{ltr}"]
                return f"{f'{val[:2]}*' if val not in {'F', 'S'} else val:^3}"

            left = " ".join(cell(l) for l in "ABC")
            right = " ".join(cell(l) for l in "DEF")
            print(f"{r:>2}   {left}   X   {right}")
        print()
