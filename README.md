# HabotConnect Booking Backend

A production-oriented REST API prototype for the HabotConnect LSA Service Booking module.

This project simulates a backend system connecting parents with Learning Support Assistants (LSAs), including LSA search, booking validation, double-booking prevention, mock payment processing, payment webhooks, automated testing, and CI/CD.

## Project Objective

The backend is designed to provide:

- Parent and LSA profile management
- LSA search by skills and availability
- Booking creation through a REST API
- Double-booking prevention
- Mock payment gateway integration
- Payment success/failure webhook handling
- Database query optimization
- Automated tests
- GitHub Actions CI

---

# Technology Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Django ORM
- Requests
- GitHub Actions
- dotenv

---

# Architecture

The project follows Django's MVT architecture with Django REST Framework used to expose RESTful APIs.

```text
Client
   |
   v
Django REST API
   |
   +----------------------+
   |                      |
   v                      v
Serializers            API Views
   |                      |
   +----------+-----------+
              |
              v
          Django ORM
              |
              v
          PostgreSQL
              |
              v
       Payment Mock Service
              |
              v
       Payment Webhook

MVT vs MVC

Django follows the MVT (Model-View-Template) architecture.

For this REST API:

Model represents database entities and relationships.
View handles HTTP requests and application logic.
Serializer handles API input/output validation.
Template is not required because this project exposes REST APIs.

Conceptually, Django's MVT maps closely to MVC, with Django's View handling much of the controller responsibility.

Database Design

The system contains three primary entities.

Parent

Stores parent information.

Fields:

id
name
email
phone
created_at
LSAProfile

Stores Learning Support Assistant information.

Fields:

id
name
email
skills
is_active
created_at

The skills field uses PostgreSQL JSON support.

BookingRequest

Stores booking information.

Fields:

id
parent
lsa
start_time
end_time
status
created_at

Booking statuses:

PENDING
CONFIRMED
PAYMENT_FAILED
CANCELLED
Relationships
Parent
  |
  | 1-to-many
  v
BookingRequest
  |
  | many-to-one
  v
LSAProfile

A parent can create multiple bookings.

An LSA can have multiple booking records.

The LSA relationship uses PROTECT so that an LSA with booking history cannot be accidentally deleted.

Database Optimization

Indexes are included for frequently queried fields.

Booking indexes
(lsa, start_time, end_time)
(parent, start_time)
status

These indexes improve filtering of bookings by LSA, time range, parent, and status.

LSA indexes
is_active
skills using PostgreSQL GIN index

The GIN index improves querying JSON-based skill data.

API Endpoints
1. Create Booking
POST /api/v1/bookings/

Creates a new booking request.

Example request:

{
    "parent": 1,
    "lsa": 1,
    "start_time": "2026-08-13T10:00:00Z",
    "end_time": "2026-08-13T11:00:00Z"
}
Validation

The API validates:

Required fields
Start time must be earlier than end time
LSA must not already have an overlapping active booking

Active booking statuses considered for overlap detection:

PENDING
CONFIRMED

If an overlap exists, the request is rejected with HTTP 400.

2. Search Available LSAs
GET /api/v1/lsas/search/

Query parameters:

skill
start_time
end_time

Example:

/api/v1/lsas/search/?skill=reading&start_time=2026-08-13T10:00:00Z&end_time=2026-08-13T11:00:00Z

The endpoint:

Filters active LSAs.
Filters LSAs by requested skill.
Checks whether an overlapping booking exists.
Returns only available LSAs.
N+1 Query Optimization

The LSA search endpoint uses Django's Exists() and OuterRef().

Conceptually:

overlapping_bookings = BookingRequest.objects.filter(
    lsa=OuterRef("pk"),
    start_time__lt=end_time,
    end_time__gt=start_time,
    status__in=[
        BookingRequest.Status.PENDING,
        BookingRequest.Status.CONFIRMED,
    ],
)

The query then annotates each LSA:

.annotate(
    has_overlap=Exists(overlapping_bookings)
)
.filter(has_overlap=False)

This allows the database to determine availability as part of the query rather than loading LSAs individually and performing separate booking queries for each LSA.

This avoids the classic N+1 query pattern.

Double-Booking Prevention

A booking overlaps an existing booking when:

existing.start_time < requested.end_time
AND
existing.end_time > requested.start_time

The serializer performs this validation before creating a booking.

Therefore, two active bookings cannot occupy the same LSA time slot through the booking API.

Payment Integration

The project includes a mock payment gateway to simulate third-party payment processing.

The payment service uses Python's requests library and includes exception handling for gateway failures.

The booking flow is:

Create Booking
      |
      v
Initiate Payment
      |
      +---- success
      |       |
      |       v
      |   Payment Webhook
      |       |
      |       v
      |    CONFIRMED
      |
      +---- failure
              |
              v
        PAYMENT_FAILED
Payment Webhook
POST /api/v1/payments/webhook/

Example request:

{
    "booking_id": 1,
    "status": "success"
}

Supported payment states:

success
failed

The webhook transitions the booking to:

success -> CONFIRMED
failed  -> PAYMENT_FAILED

The webhook uses:

transaction.atomic()

and:

select_for_update()

to safely update the booking while protecting against concurrent updates.

Error Handling

The API returns appropriate HTTP status codes.

Examples:

200 OK
201 CREATED
400 BAD REQUEST
402 PAYMENT REQUIRED
404 NOT FOUND
502 BAD GATEWAY

External payment failures are handled using a custom payment gateway exception.

Logging is used when the mock payment webhook request fails.

Automated Testing

The project contains automated Django REST API tests covering success, validation, edge, and failure scenarios.

The test suite covers:

Booking creation
Invalid booking time
Double-booking prevention
LSA search
Missing search parameters
Payment webhook success
Payment webhook failure
Invalid webhook data

Run tests locally:

python manage.py test

Current test suite:

8 tests

All tests pass locally.

GitHub Actions CI

The repository contains a GitHub Actions workflow:

.github/workflows/tests.yml

The workflow automatically:

Checks out the repository.
Sets up Python.
Starts PostgreSQL.
Installs dependencies.
Runs Django system checks.
Runs the automated test suite.

The CI workflow has been successfully executed on GitHub.

Environment Variables

Create a .env file locally.

Example:

DJANGO_SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=your_database
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432

PAYMENT_GATEWAY_URL=your_payment_gateway_url

Do not commit real credentials or secrets to Git.

Local Setup

Clone the repository:

git clone https://github.com/AkshayGor2006/habot-booking-backend.git
cd habot-booking-backend

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Run migrations:

python manage.py migrate

Run Django checks:

python manage.py check

Run tests:

python manage.py test

Start the development server:

python manage.py runserver

The local API will be available at:

http://127.0.0.1:8000/
Project Structure
habot-booking-backend/
│
├── bookings/
│   ├── migrations/
│   ├── services/
│   ├── models.py
│   ├── serializers.py
│   ├── lsa_serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
Engineering Decisions
Django + DRF

Django provides a mature ORM, migrations, validation ecosystem, and project structure. Django REST Framework provides serializers and REST API support.

PostgreSQL

PostgreSQL provides relational integrity and efficient indexing, including GIN indexes for JSON data.

Exists() for availability

Exists() allows the database to efficiently determine whether an LSA has an overlapping booking without performing a separate query for every LSA.

Transaction locking

transaction.atomic() and select_for_update() protect booking state transitions during payment webhook processing.

Automated CI

GitHub Actions ensures that tests and Django checks are executed automatically whenever changes are pushed.

Repository

GitHub:

https://github.com/AkshayGor2006/habot-booking-backend

Author

Akshay Gor

Python Backend Developer Candidate

HabotConnect Hiring Project — 2026