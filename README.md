# HABOT Booking Backend

A Django REST Framework backend for an LSA (Learning Support Assistant) booking system.

## Features

- LSA profile management
- LSA search by skill and availability
- Booking creation
- Time-slot conflict prevention
- Mock payment processing
- Payment webhook handling
- Booking confirmation workflow
- REST API endpoints
- Environment-based configuration

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- REST APIs
- Git & GitHub

## Booking Flow

LSA Search
↓
Booking Creation
↓
Payment Initiation
↓
Payment Success
↓
Payment Webhook
↓
Booking Confirmation

## API Endpoints

### Search LSA

```text
GET /api/v1/lsas/search/

Example:

/api/v1/lsas/search/?skill=math&start_time=2026-08-25T10:00:00Z&end_time=2026-08-25T11:00:00Z
Create Booking
POST /api/v1/bookings/
Mock Payment
POST /api/mock-payment/charge/
Payment Webhook
POST /api/v1/payments/webhook/
Setup

Clone the repository:

git clone https://github.com/AkshayGor2006/habot-booking-backend.git
cd habot-booking-backend

Create a virtual environment:

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

Install dependencies:

pip install django djangorestframework psycopg2-binary python-dotenv requests

Create a .env file and configure your database credentials.

Run migrations:

python manage.py migrate

Start the server:

python manage.py runserver

The API will be available at:

http://127.0.0.1:8000/
Testing

Run Django checks:

python manage.py check

Run tests:

python manage.py test