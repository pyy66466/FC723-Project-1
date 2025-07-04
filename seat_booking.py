from __future__ import annotations
from typing import Dict

# -------- Aircraft-level constants (one airframe, global) ----------
LETTERS: str = "ABCDEF"                # Seat letters per row
ROWS = range(1, 81)                    # Row numbers 1-80
STORAGE_ROWS = {77, 78}                # Rear storage rows
STORAGE_COLS = {"D", "E", "F"}         # Storage columns

SeatMap = Dict[str, str]               # e.g. {"1A": "F"}


class SeatBookingSystem:
    """Core booking class.  Status codes: F = Free, R = Reserved, S = Storage."""

    def __init__(self) -> None:
        self.seats: SeatMap = {}
        self._init_seats()

    # ---------------- internal helpers ----------------
    def _init_seats(self) -> None:
        for row in ROWS:
            for letter in LETTERS:
                code = f"{row}{letter}"
                self.seats[code] = (
                    "S"
                    if row in STORAGE_ROWS and letter in STORAGE_COLS
                    else "F"
                )

    # ---------------- validation ----------------------
    def normalise_seat(self, code: str) -> str:
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

    def book_seat(self, code: str) -> bool:
        code = self.normalise_seat(code)
        if self.is_free(code):
            self.seats[code] = "R"
            return True
        return False

    def free_seat(self, code: str) -> bool:
        code = self.normalise_seat(code)
        if self.seats[code] == "R":
            self.seats[code] = "F"
            return True
        return False

    # ---------------- reporting -----------------------
    def summary(self) -> Dict[str, int]:
        counts = {"F": 0, "R": 0, "S": 0}
        for status in self.seats.values():
            counts[status] += 1
        return {
            "free": counts["F"],
            "reserved": counts["R"],
            "storage": counts["S"],
        }

    def print_chart(self) -> None:
        print("\nLEGEND  F = free   R = reserved   S = storage   X = aisle\n")
        for row in ROWS:
            left = " ".join(
                f"{row:>2}{ltr}:{self.seats[f'{row}{ltr}']}" if self.seats[f'{row}{ltr}'] != "S"
                else "   S" for ltr in "ABC"
            )
            right = " ".join(
                f"{row:>2}{ltr}:{self.seats[f'{row}{ltr}']}" if self.seats[f'{row}{ltr}'] != "S"
                else "   S" for ltr in "DEF"
            )
            print(f"{left}  X  {right}")
        print()
