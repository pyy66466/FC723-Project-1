import pytest
from seat_booking import SeatBookingSystem


# ---------------- fixtures ----------------
@pytest.fixture
def empty_plane() -> SeatBookingSystem:
    return SeatBookingSystem()


@pytest.fixture
def half_full_plane() -> SeatBookingSystem:
    sys = SeatBookingSystem()
    for code in ["1A", "1B", "1C", "2A"]:
        sys.book_seat(code)
    return sys


# ---------------- unit tests --------------
def test_validation(empty_plane):
    with pytest.raises(ValueError):
        empty_plane.seat_status("0Z")
    with pytest.raises(ValueError):
        empty_plane.book_seat("77E")  # storage seat


def test_single_booking_cycle(empty_plane):
    assert empty_plane.book_seat("3A") is True
    assert empty_plane.book_seat("3A") is False  # already booked
    assert empty_plane.free_seat("3A") is True
    assert empty_plane.free_seat("3A") is False  # already free


def test_adjacent_booking_success(empty_plane):
    seats = empty_plane.book_adjacent(3)
    assert seats and len(seats) == 3
    assert all(empty_plane.seat_status(s) == "R" for s in seats)


def test_adjacent_booking_failure(half_full_plane):
    # row 1 ABC is blocked, so group of 3 must not be in that block
    seats = half_full_plane.book_adjacent(3)
    assert seats
    assert not any(s.startswith("1") and s[-1] in "ABC" for s in seats)


def test_summary_counts(empty_plane):
    empty_plane.book_adjacent(2)
    summary = empty_plane.summary()
    assert summary["reserved"] == 2
    total_seats = 80 * 6
    assert sum(summary.values()) == total_seats
