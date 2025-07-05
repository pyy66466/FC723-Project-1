import sqlite3
import pytest
from seat_booking import SeatBookingSystem

# ---------------- Fixtures ----------------
@pytest.fixture
def empty_plane(tmp_path):
    return SeatBookingSystem(str(tmp_path / "test_empty.db"))

@pytest.fixture
def half_full_plane(tmp_path):
    sys = SeatBookingSystem(str(tmp_path / "test_half.db"))
    for code in ["1A", "1B", "1C", "2A"]:
        sys.book_seat(code, "PZ", "Half", "Full")
    return sys

# ---------------- Unit Tests ----------------
def test_validation(empty_plane):
    with pytest.raises(ValueError):
        empty_plane.seat_status("0Z")
    with pytest.raises(ValueError):
        empty_plane.book_seat("77E", "PP", "F", "L")  # storage seat

def test_single_booking_cycle(empty_plane):
    assert empty_plane.book_seat("3A", "PX", "Foo", "Bar") is not None
    assert empty_plane.book_seat("3A", "PY", "Bar", "Baz") is None  # already booked
    assert empty_plane.free_seat("3A") is True
    assert empty_plane.free_seat("3A") is False  # already free

def test_adjacent_3_passengers(empty_plane):
    passengers = [
        ("PA1", "A1", "Z"),
        ("PA2", "A2", "Z"),
        ("PA3", "A3", "Z"),
    ]
    seats_refs = empty_plane.book_adjacent(passengers)
    assert seats_refs and len(seats_refs) == 3
    ref = seats_refs[0][1]
    for seat, r in seats_refs:
        assert empty_plane.seat_status(seat) == ref

def test_adjacent_booking_failure(half_full_plane):
    passengers = [
        ("P1", "B1", "C"),
        ("P2", "B2", "C"),
        ("P3", "B3", "C"),
    ]
    seats_refs = half_full_plane.book_adjacent(passengers)
    assert seats_refs is not None
    assert not any(s.startswith("1") and s[-1] in "ABC" for s, _ in seats_refs)

def test_summary_counts(empty_plane):
    passengers = [("PX", "F", "L"), ("PY", "G", "M")]
    empty_plane.book_adjacent(passengers)
    summary = empty_plane.summary()
    assert summary["reserved"] == 2
    assert summary["free"] + summary["reserved"] + summary["storage"] == 80 * 6

def test_db_load(tmp_path):
    db_file = tmp_path / "pre.db"
    con = sqlite3.connect(db_file)
    con.execute("CREATE TABLE booking(ref TEXT, passport TEXT, first_name TEXT, last_name TEXT, row INT, col TEXT)")
    con.execute("INSERT INTO booking VALUES('REF12345','PZ','Old','Rec',10,'B')")
    con.commit()
    con.close()

    sys = SeatBookingSystem(str(db_file))
    assert sys.seat_status("10B") == "REF12345"
