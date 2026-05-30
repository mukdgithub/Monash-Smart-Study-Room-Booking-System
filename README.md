# Monash Smart Study Room Booking System (MSSRB)

## Project Overview

The Monash Smart Study Room Booking System (MSSRB) is a text-based application developed as part of FIT5136 Software Engineering.

The system enables students to:
- Register and manage accounts
- Log in securely
- Browse and filter study rooms
- Make and cancel room bookings
- Manage account funds
- Review booking history
- Purchase and apply deal packages

The system also enables administrators to:
- Add, update, and remove study rooms
- Manage room availability
- Monitor booking status

The application follows Object-Oriented Programming (OOP) principles and stores data using CSV/Text files without using any database.

---

## Technologies Used

- Programming Language: Python 3.13.x / Java 23.x
- IDE: PyCharm / IntelliJ IDEA
- Version Control: GitLab
- Project Management: Trello
- Design Tool: Lucidchart

---

## Features

### Feature 1: User Management
- Student registration
- Student login
- Profile management
- Booking history viewing
- Funds management

### Feature 2: Room Management
- Create rooms
- Update rooms
- Delete rooms
- Manage room availability
- Manage room pricing
- Manage room equipment

### Feature 3: Booking Management
- View available rooms
- Filter rooms
- Make booking
- Cancel booking

### Feature 4: Checkout and Payment
- Booking review
- Payment processing
- Deal package application
- Booking confirmation

---

## Project Structure

MSSRB/

├── data/

│   ├── students.csv

│   ├── rooms.csv

│   ├── bookings.csv

│   ├── payments.csv

│   └── deals.csv

│

├── src/

│   ├── models/

│   ├── controllers/

│   ├── services/

│   ├── utils/

│   └── main.py

│

├── docs/

│   ├── SRS.pdf

│   ├── InitialClassDiagram.pdf

│   ├── DetailedClassDiagram.pdf

│   ├── SequenceDiagram.pdf

│   └── FoundationModelsUsed.pdf

│

├── README.md

│

└── requirements.txt (if applicable)

---

## Installation Guide

### Python Version

Ensure Python 3.13.x is installed.

Check version:

```bash
python --version
```

or

```bash
python3 --version
```

### Clone Repository

```bash
git clone <repository-url>
```

Navigate to project folder:

```bash
cd MSSRB
```

### Running the Application

Execute:

```bash
python main.py
```

or

```bash
python3 main.py
```

---

## Default Test Accounts

### Student

Username:
```text
student1
```

Password:
```text
pass1234
```

### Administrator

Username:
```text
admin1
```

Password:
```text
admin123
```

---

## Sample Workflow

### Student

1. Register account
2. Login
3. Add funds
4. Browse rooms
5. Select room
6. Select timeslot
7. Review booking
8. Confirm booking
9. View booking history

### Administrator

1. Login
2. Add room
3. Update room details
4. Manage availability
5. Remove room

---

## Business Rules

- A room cannot be double-booked.
- Students must have sufficient balance before booking.
- Duplicate student accounts are not allowed.
- Invalid inputs are rejected.
- Bookings cannot be created for unavailable timeslots.
- Room availability is updated automatically after booking.

---

## Data Storage

The application uses CSV/Text files only.

No database systems are used, following project requirements.

Example files:
- students.csv
- rooms.csv
- bookings.csv
- payments.csv
- deals.csv

---

## Error Handling

The system validates all user inputs and provides user-friendly messages for:

- Invalid login credentials
- Duplicate registration
- Insufficient balance
- Room unavailability
- Invalid room selection
- Invalid menu options
- Missing data

---

## Testing

The following scenarios have been tested:

### Registration
- Valid registration
- Duplicate account prevention

### Login
- Successful login
- Invalid credentials

### Booking
- Successful booking
- Double-booking prevention
- Insufficient funds

### Room Management
- Add room
- Update room
- Delete room

### Payment
- Successful payment
- Failed payment handling

---

## Assumptions

- Users are Monash students or administrators.
- All room and booking data are stored locally.
- Internet connectivity is not required.
- The application runs through a terminal/command-line interface.

---

## Troubleshooting

### Problem: Application does not start

Solution:
- Verify Python 3.13.x is installed.
- Verify all project files have been cloned correctly.

### Problem: CSV file not found

Solution:
- Ensure all CSV files are located inside the data folder.
- Verify file names match those expected by the program.

### Problem: Changes are not being saved

Solution:
- Ensure write permissions are enabled for CSV files.
- Verify the application closes normally after updates.
