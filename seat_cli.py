from seat_booking import SeatBookingSystem


def main() -> None:
    sys = SeatBookingSystem()
    menu = """
=== BURAK 757 SEAT BOOKING ===
1. Check seat availability
2. Book seat (single)
3. Free seat
4. Book adjacent seats (2-3)
5. Show seating chart
6. Exit
Choice: """

    while True:
        try:
            choice = int(input(menu))
        except ValueError:
            print("Please a number 1-6\n")
            continue

        if choice == 1:
            code = input("Seat code: ")
            try:
                print(f"{code.upper()} → {sys.seat_status(code)}\n")
            except ValueError as e:
                print(f"{e}\n")

        elif choice == 2:
            code = input("Seat code to book: ")
            pno  = input("Passport no: ")
            fn   = input("First name : ")
            ln   = input("Last name  : ")
            try:
                ref  = sys.book_seat(code, pno, fn, ln)
                if ref:
                    print("\nBooking successful:\n")

                    print(f"  Passenger: {fn} {ln} | Passport: {pno}")
                    print(f"  Seat: {code} | Booking Reference: {ref}\n")
                else:
                    print(f"Seat {code} is not available\n")
            except ValueError as e:
                print(f"{e}\n")

        elif choice == 3:
            code = input("Seat code to free: ")
            try:
                print(f"The reservation of seat {code} is successfully cancelled\n" if sys.free_seat(code) else f"Seat {code} was not reserved\n")
            except ValueError as e:
                print(f"{e}\n")

        elif choice == 4:
            try:
                n = int(input("Group size (2 or 3): "))
                passengers: list[tuple[str, str, str]] = []
                for i in range(1, n + 1):
                    print(f"\nPassenger {i}:")
                    pno = input("  Passport no: ")
                    fn  = input("  First name : ")
                    ln  = input("  Last name  : ")
                    passengers.append((pno, fn, ln))

                seats_refs = sys.book_adjacent(passengers)
                if seats_refs:
                    print("\nBooking successful:\n")
                    for (seat, ref), (pno, fn, ln) in zip(seats_refs, passengers):
                        print(f"  Passenger: {fn} {ln} | Passport: {pno}")
                        print(f"  Seat: {seat} | Booking Reference: {ref}\n")
                else:
                    print("No adjacent block available.\n")
            except ValueError as e:
                print(e, "\n")

        elif choice == 5:
            sys.print_chart()

        elif choice == 6:
            break

        else:
            print("Please select a valid choice\n")


if __name__ == "__main__":
    main()
