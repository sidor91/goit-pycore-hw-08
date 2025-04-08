import re
from collections import UserDict
from dataclasses import dataclass
from datetime import datetime, timedelta
import pickle


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Error: {str(e)}"

    return inner


def parse_input(user_input):
    try:
        cmd, *args = user_input.split()
        cmd = cmd.strip().lower()
        return cmd, *args
    except ValueError:
        raise ValueError("There are no arguments passed")


@dataclass
class Field:
    value: str

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, name: str):
        if len(name) < 2:
            raise ValueError("Name should contain at least 2 characters")
        super().__init__(name)


class Phone(Field):
    validate_phone_error_msg = (
    "The phone should optionally contain country code (1-3 digits with/withount +) "
    "and mandatory contain a regional code (1-4 digits with/without brackets()) followed by up to 9 digits. "
    "Allowed separators are ' ', '-', '.'"
    )

    def __init__(self, phone: str):
        if not self.is_valid_phone(phone):
            raise ValueError(self.validate_phone_error_msg)
        super().__init__(phone)

    def is_valid_phone(self, phone):
        pattern = r"^\+?\d{1,3}?[-.\s]?(\(\d{1,4}\)|\d{1,4})[-.\s]?\d{1,4}[-.\s]?\d{1,9}$"
        return bool(re.fullmatch(pattern, phone))


class Birthday(Field):
    def __init__(self, value):
        date = self.parse_date(value)
        if date is None:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

    def parse_date(self, date_str: str) -> datetime | None:
        try:
            return datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError:
            return None


class Record:
    def __init__(self, name):
        self.name: Name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday = None

    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    @input_error
    def remove_phone(self, phone):
        existing_phone = self.find_phone(phone)
        if existing_phone:
            self.phones.remove(existing_phone)
            return "Phone has been removed"
        else:
            raise ValueError(f"Phone {phone} not found")

    @input_error
    def change_phone(self, phone: str, new_phone: str):
        existing_phone = self.find_phone(phone)

        if not existing_phone:
            raise ValueError(f"Phone {phone} not found")

        new_phone_item = Phone(new_phone)
        self.phones[self.phones.index(existing_phone)] = new_phone_item
        return "Contact changed."

    def find_phone(self, phone: str) -> Phone:
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    @input_error
    def add_birthday(self, birthday: str) -> None:
        if self.birthday:
            raise ValueError("Birthday already exists")
        self.birthday = Birthday(birthday)
        return "Birthday added"

    def __str__(self):
        message = f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"
        if self.birthday:
            message += f", birthday: {self.birthday.value}"
        return message


class AddressBook(UserDict):

    @input_error
    def add_record(self, args: list[str]) -> None:
        if len(args) < 2:
            raise ValueError(
                '"add" command should contain 2 arguments "name" and "phone number"'
            )
        name, phone = args[0], args[1]
        existing_contact: Record = self.data.get(name, f"User {name} not found")
        if isinstance(existing_contact, str):
            new_record = Record(name)
            new_record.add_phone(phone)
            self.data[name] = new_record
            return f"Contact {name} added"
        else:
            existing_contact_phones = existing_contact.phones
            if Phone(phone) in existing_contact_phones:
                raise ValueError(f"The phone {phone} already exists in contact {name}")
            else:
                existing_contact.add_phone(phone)
                return f"New phone for contact {name} has been added"

    @input_error
    def find(self, args: list[str]) -> Record | str:
        if not args:
            raise ValueError("Contact name missing")
        name = args[0]
        contact = self.data.get(name, f"User {name} not found")

        if isinstance(contact, str):
            raise ValueError(contact)

        return contact

    @input_error
    def delete(self, args: list[str]):
        if not args:
            raise ValueError("Contact name missing")
        name = args[0]
        self.data.pop(name, f"User {name} not found")
        return f"Contact {name} deleted"

    def __str__(self):
        return (
            "\n".join(str(record) for record in self.data.values())
            if self.data
            else "No contacts available"
        )

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        next_week = today + timedelta(days=7)
        upcoming_birthdays = []
        all_users: list[Record] = self.data.values()

        for user in all_users:
            if not user.birthday:
                continue
            birthday = datetime.strptime(user.birthday.value, "%d.%m.%Y").date()
            birthday_this_year = birthday.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if today <= birthday_this_year <= next_week:
                if birthday_this_year.weekday() in [5, 6]:
                    birthday_this_year += timedelta(
                        days=(7 - birthday_this_year.weekday())
                    )

                upcoming_birthdays.append(
                    {
                        "name": user.name.value,
                        "congratulation_date": birthday_this_year.strftime("%d.%m.%Y"),
                    }
                )

        return upcoming_birthdays
    
    def save_data(book, filename="addressbook.pkl"):
       with open(filename, "wb") as f:
        pickle.dump(book, f)

    @staticmethod
    def load_data(filename="addressbook.pkl"):
      try:
        with open(filename, "rb") as f:
            return pickle.load(f)
      except FileNotFoundError:
        return AddressBook()


def main():
    book = AddressBook.load_data()

    print("Welcome to the assistant bot!")

    while True:
        try:
            user_input = input("Enter a command: ")
            command, *args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                book.save_data()
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(book.add_record(args))

            elif command == "all":
                print(book)

            elif command == "phone":
                print(book.find(args))

            elif command == "delete":
                print(book.delete(args))

            elif command == "change":
                if len(args) < 3:
                    raise ValueError(
                        "'change' command should contain 3 arguments: name, old_phone, new_phone"
                    )
                contact = book.find(args)
                print(contact.change_phone(args[1], args[2]))

            elif command == "add-birthday":
                if len(args) < 2:
                    raise ValueError(
                        '"add-birthday" command should contain 2 arguments "name" and "birthday" in format DD.MM.YYYY'
                    )
                contact = book.find(args)
                print(contact.add_birthday(args[1]))

            elif command == "show-birthday":
                contact = book.find(args)
                if contact.birthday:
                    print(f"Birthday: {contact.birthday}")
                else:
                    print(f"Birthday for contact {args[0]} hasn't been set")

            elif command == "birthdays":
                print(book.get_upcoming_birthdays())

            else:
                print("Invalid command.")
        except ValueError as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
