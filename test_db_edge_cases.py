import sqlite3
from glob import glob
from pathlib import Path

import pytest
from seat_booking import SeatBookingSystem


# ------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------
def columns_in_db(db_file):
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute("PRAGMA table_info(booking)")
    cols = [row[1] for row in cur.fetchall()]
    con.close()
    return set(cols)


# ============================================================
# E1  In‑memory fallback when db_path is None / ''
# ============================================================
@pytest.mark.parametrize("param", [None, ""])
def test_in_memory_db(param):
    sys = SeatBookingSystem(db_path=param)
    ref = sys.book_seat("1A", "P1", "A", "B")
    assert ref and len(ref) == 8


# ============================================================
# E2  Non‑existing folder is auto‑created
# ============================================================
def test_missing_folder_created(tmp_path):
    deep = tmp_path / "folder1" / "folder2" / "booking.db"
    sys = SeatBookingSystem(deep)
    assert deep.exists()        # file created
    assert deep.parent.exists() # nested dirs created
    sys.book_seat("2A", "P2", "C", "D")


# ============================================================
# E3  Corrupt (non‑SQLite) file is quarantined, new DB made
# ============================================================
def test_corrupt_file_quarantined(tmp_path):
    db_file = tmp_path / "bad.db"
    db_file.write_text("this is not sqlite")

    SeatBookingSystem(db_file)  # constructor should not raise
    # original file should be renamed *.corrupt-YYYYMMDD-HHMM.db
    renamed = glob(str(db_file.with_suffix(".corrupt-*db")))
    assert renamed, "corrupt file should be renamed"
    assert Path(db_file).exists(), "fresh DB should now exist"


# ============================================================
# E4  Existing SQLite but NO booking table → table created
# ============================================================
def test_missing_table_added(tmp_path):
    db_file = tmp_path / "no_table.db"
    sqlite3.connect(db_file).close()          # empty file
    SeatBookingSystem(db_file)
    assert {"ref","passport","row","col"} <= columns_in_db(db_file)


# ============================================================
# E5  Booking table missing columns → columns auto‑added
# ============================================================
def test_missing_columns_altered(tmp_path):
    db_file = tmp_path / "missing_cols.db"
    con = sqlite3.connect(db_file)
    con.execute("CREATE TABLE booking (ref TEXT PRIMARY KEY, passport TEXT)")
    con.commit()
    con.close()

    SeatBookingSystem(db_file)
    assert {"row", "col", "first_name", "last_name"} <= columns_in_db(db_file)


# ============================================================
# E6  Existing records loaded into seat map
# ============================================================
def test_existing_records_loaded(tmp_path):
    db_file = tmp_path / "prepop.db"
    con = sqlite3.connect(db_file)
    con.execute(
        """CREATE TABLE booking (
               ref TEXT PRIMARY KEY,
               passport TEXT,
               first_name TEXT,
               last_name TEXT,
               row INTEGER,
               col TEXT)"""
    )
    con.execute(
        "INSERT INTO booking VALUES "
        "('ABC12345', 'P999', 'Eva', 'Ng', 10, 'B')"
    )
    con.commit()
    con.close()

    sys = SeatBookingSystem(db_file)
    assert sys.seat_status("10B") == "ABC12345"
