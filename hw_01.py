from collections import UserDict
import re
from datetime import datetime
import pickle
from abc import ABC, abstractmethod

class UserView(ABC):
    @abstractmethod
    def display_contacts(self, contacts):
        pass

    @abstractmethod
    def display_commands(self, commands):
        pass

    @abstractmethod
    def display_message(self, message):
        pass

class ConsoleView(UserView):
    def display_contacts(self, contacts):
        if contacts:
            print("Contacts:")
            for contact in contacts:
                print(contact)
        else:
            print("No contacts found.")

    def display_commands(self, commands):
        print("Available commands:")
        for command in commands:
            print(f"- {command}")

    def display_message(self, message):
        print(message)

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name cannot be empty")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        self.validate_phone(value)
        super().__init__(value)

    def validate_phone(self, value):
        if not re.match(r'^\d{10}$', value):
            raise ValueError("Phone number must be 10 digits long")

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_to_remove = next((p for p in self.phones if p.value == phone), None)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone, new_phone):
        phone_to_edit = next((p for p in self.phones if p.value == old_phone), None)
        if phone_to_edit:
            self.remove_phone(old_phone)
            self.add_phone(new_phone)

    def find_phone(self, phone):
        return next((p.value for p in self.phones if p.value == phone), None)

    def add_birthday(self, birthday):
        self.birthday = birthday

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones)
        birthday = str(self.birthday) if self.birthday else "No birthday"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday:
                next_birthday = record.birthday.value.replace(year=today.year)
                if next_birthday < today:
                    next_birthday = next_birthday.replace(year=today.year + 1)
                days_until_birthday = (next_birthday - today).days
                if 0 <= days_until_birthday <= 6:
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": str(next_birthday),
                        "days_until_birthday": days_until_birthday
                    })
        return upcoming_birthdays

    def __str__(self):
        return '\n'.join(str(record) for record in self.data.values())
    
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)
        
def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return str(e)
    return wrapper

def parse_input(user_input):
    parts = user_input.split()
    return parts[0], parts[1:]

@input_error
def add(args, book):
    if len(args) < 2:
        return "Usage: add [name] [phone]"
    name, phone = args
    if name in book.data:
        book.data[name].add_phone(phone)
        return f"Phone {phone} added to {name}."
    else:
        record = Record(name)
        record.add_phone(phone)
        book.add_record(record)
        return f"Contact {name} with phone {phone} added."

@input_error
def change(args, book):
    if len(args) < 3:
        return "Usage: change [name] [old phone] [new phone]"
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone {old_phone} changed to {new_phone} for {name}."
    return "Contact not found."

@input_error
def phone(args, book):
    name = args[0]
    record = book.find(name)
    if record:
        return f"Phones for {name}: {', '.join(p.value for p in record.phones)}"
    return "Contact not found."

@input_error
def all_contacts(args, book):
    return str(book) if book.data else "Address book is empty."

@input_error
def add_birthday(args, book):
    name, date_str = args
    if name not in book.data:
        return "Contact not found."
    try:
        birthday = Birthday(date_str)
        book.data[name].add_birthday(birthday)
        return f"Birthday added for {name}."
    except ValueError as e:
        return str(e)

@input_error
def show_birthday(args, book):
    name = args[0]
    if name not in book.data:
        return "Contact not found."
    record = book.data[name]
    return f"{name}'s birthday is {record.birthday}" if record.birthday else f"{name} has no birthday set."

@input_error
def birthdays(args, book):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays in the next 7 days."
    result = []
    for entry in upcoming_birthdays:
        result.append(f"Name: {entry['name']}, Birthday: {entry['birthday']}")
    return "\n".join(result)

def main():
    book = load_data()
    view = ConsoleView()

    print("Welcome to the assistant bot!")

     # Створення запису для John
    john_record = Record("John")
    john_record.add_phone("1234567890")
    john_record.add_phone("5555555555")
    john_record.add_birthday(Birthday("10.08.1990"))

    # Додавання запису John до адресної книги
    book.add_record(john_record)

    # Створення та додавання нового запису для Jane
    jane_record = Record("Jane")
    jane_record.add_phone("9876543210")
    jane_record.add_birthday(Birthday("15.08.1992"))
    book.add_record(jane_record)

    # Виведення всіх записів у книзі
    print("Address Book:")
    print(book)

    # Знаходження та редагування телефону для John
    john = book.find("John")
    if john:
        john.edit_phone("1234567890", "1112223333")

    print("\nUpdated John Record:")
    print(john)  # Виведення: Contact name: John, phones: 1112223333; 5555555555

    # Пошук конкретного телефону у записі John
    found_phone = john.find_phone("5555555555")
    print(f"\nFound Phone for John: {found_phone}")  # Виведення: 5555555555

    #
    print("Address Book:")
    print(book)

    # Видалення запису Jane
    book.delete("Jane")

    print("\nAddress Book after deleting Jane:")
    print(book)
    #
    print("\nUpcoming Birthdays:")
    print(birthdays([], book))


    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            view.display_message("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            view.display_message("How can I help you?")

        elif command == "add":
            result = add(args, book)
            view.display_message(result)

        elif command == "change":
            result = change(args, book)
            view.display_message(result)

        elif command == "phone":
            result = phone(args, book)
            view.display_message(result)

        elif command == "all":
            view.display_contacts(book.data.values())

        elif command == "add-birthday":
            result = add_birthday(args, book)
            view.display_message(result)

        elif command == "show-birthday":
            result = show_birthday(args, book)
            view.display_message(result)

        elif command == "birthdays":
            result = birthdays(args, book)
            view.display_message(result)

        else:
            view.display_message("Invalid command.")

###

# Створення нової адресної книги
if __name__ == "__main__":
    main()