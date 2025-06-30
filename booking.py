"""
Burak 757 seat-booking console application
==========================================

Module Name: Programming Theory
Module Code: FC723
Tutor's Name: Sophie Norman
Student GUID Number: P472969

==========================================

Specification
-------------------
* Seat code format: <row><letter>, e.g. 1A
* Valid rows: 1-80 ; valid letters: A-F
* Status codes:
    F = free
    R = reserved
    S = storage (permanently unavailable, rows 77-78 seats D-F)
* An aisle separates seats C and D; the aisle itself is NOT a seat.

Menu
----
1. Check availability
2. Book a seat
3. Free (cancel) a seat
4. Show full seating chart
5. Exit
"""

from typing import Dict

# --------------------------------------------------------------------------- #
#                              DATA STRUCTURES                                #
# --------------------------------------------------------------------------- #
SeatMap = Dict[str, str]        # e.g. {"1A": "F", "2A": "R", ...}
LETTERS = "ABCDEF"
ROWS = range(1, 81)             # 1 .. 80 inclusive


def make_initial_seatmap() -> SeatMap:
    """
    Initialise seat status.

    Every seat is free ('F') unless it is in the fixed storage area
    (rows 77-78, seats D/E/F), in which case it is 'S'.
    """
    seats: SeatMap = {}
    for row in ROWS:
        for letter in LETTERS:
            code = f"{row}{letter}"
            
            # Mark storage seats as permanently unavailable
            if letter in "DEF" and row in (77, 78):
                seats[code] = "S"
            else:
                seats[code] = "F"
    return seats


SEATS = make_initial_seatmap()


# --------------------------------------------------------------------------- #
#                              CORE UTILITIES                                 #
# --------------------------------------------------------------------------- #
def normalise_seat(code: str) -> str:
    """
    Clean user input (e.g. ' 12c ') → '12C'.  Raises ValueError if invalid.
    """
    code = code.strip().upper()

    # Check format: last char must be letter, rest must be digits
    if not code or not code[-1].isalpha() or not code[:-1].isdigit():
        raise ValueError("Seat code must be like 12C or 3F")

    row = int(code[:-1])
    letter = code[-1]

    if row not in ROWS or letter not in LETTERS:
        raise ValueError("Seat code outside valid range (1-80, A-F)")

    full_code = f"{row}{letter}"
    if SEATS[full_code] == "S":
        raise ValueError(f"{full_code} is a storage area and cannot be booked")

    return full_code


def is_free_seat(code: str) -> bool:
    """Return True if the seat exists and is not booked (R)."""
    return SEATS[code] == "F"


def book_seat(code: str) -> bool:
    """
    Attempt to book seat by `code`.
    Returns True if booking succeeds, False if already reserved.
    (Storage seats are filtered out during normalise_seat()).
    """
    if is_free_seat(code):
        SEATS[code] = "R"
        return True
    return False


def free_seat(code: str) -> bool:
    """
    Attempt to release / cancel `code`.
    Returns True if the seat was previously booked, False otherwise.
    """
    if SEATS[code] == "R":
        SEATS[code] = "F"
        return True
    return False


# --------------------------------------------------------------------------- #
#                              PRESENTATION                                   #
# --------------------------------------------------------------------------- #
def display_booking_status() -> None:
    """Pretty-print the booking layout with legend."""
    print("\nLEGEND  F = free   R = reserved   S = storage\n")

    # Loop rows numerically for a natural view: 1 (front) → 80 (rear)
    for row in ROWS:
        left = " ".join(f"{row}{ltr}:\t{SEATS[f'{row}{ltr}']}\t"
                        for ltr in "ABC")
        right = " ".join(f"{row}{ltr}:\t{SEATS[f'{row}{ltr}']}\t"
                         for ltr in "DEF")
        print(f"{left}X\t{right}")
    print()  # extra newline for readability


# --------------------------------------------------------------------------- #
#                              USER INTERFACE                                 #
# --------------------------------------------------------------------------- #
def main() -> None:
    """Main menu loop."""
    MENU = """
================= BURAK 757 SEAT BOOKING =================
1. Check availability
2. Book a seat
3. Free a seat
4. Show booking status
5. Exit
Choice: """
    while True:
        try:
            choice = int(input(MENU))
        except ValueError:
            print("Please enter a number between 1 and 5.\n")
            continue

        if choice == 1:
            seat = input("Please enter seat to check (e.g. 1A): ")
            try:
                seat = normalise_seat(seat)
                status = SEATS[seat]
                msg = ("AVAILABLE" if status == "F"
                       else "UNAVAILABLE: RESERVED"
                       if status == "R"
                       else "UNAVAILABLE: STORAGE AREA")
                print(f"{seat} is {msg}\n")
            except ValueError as err:
                print(f"{err}\n")

        elif choice == 2:
            seat = input("Please enter seat to book: ")
            try:
                seat = normalise_seat(seat)
                if book_seat(seat):
                    print(f"Congrats! {seat} is successfully booked!\n")
                else:
                    print(f"Sorry! {seat} is already taken!\n")
            except ValueError as err:
                print(f"{err}\n")

        elif choice == 3:
            seat = input("Please enter seat to free: ")
            try:
                seat = normalise_seat(seat)
                if free_seat(seat):
                    print(f"{seat} reservation cancelled.\n")
                else:
                    print(f"{seat} was not reserved.\n")
            except ValueError as err:
                print(f"{err}\n")

        elif choice == 4:
            display_booking_status()

        elif choice == 5:
            print("Goodbye, and thank you for flying Apache Airlines!")
            break

        else:
            print("Invalid menu choice.\n")


# --------------------------------------------------------------------------- #
#                             SCRIPT ENTRYPOINT                               #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
