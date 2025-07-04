from seat_booking import SeatBookingSystem


def main() -> None:
    sys = SeatBookingSystem()
    menu = """
=== BURAK 757 SEAT BOOKING ===
1. Check availability
2. Book seat
3. Free seat
4. Show seating chart
5. Exit
Choice: """

    while True:
        try:
            choice = int(input(menu))
        except ValueError:
            print("Please a number 1-5\n")
            continue

        if choice == 1:
            code = input("Seat code: ")
            try:
                print(f"{code.upper()} → {sys.seat_status(code)}\n")
            except ValueError as e:
                print(f"{e}\n")

        elif choice == 2:
            code = input("Seat code to book: ")
            try:
                print(f"Seat {code} is successfully booked\n" if sys.book_seat(code) else f"Seat {code} is not available\n")
            except ValueError as e:
                print(f"{e}\n")

        elif choice == 3:
            code = input("Seat code to free: ")
            try:
                print(f"The reservation of seat {code} is successfully cancelled\n" if sys.free_seat(code) else f"Seat {code} was not reserved\n")
            except ValueError as e:
                print(f"{e}\n")

        elif choice == 4:
            sys.print_chart()

        elif choice == 5:
            break

        else:
            print("Please select a valid choice\n")


if __name__ == "__main__":
    main()
