#  Farm2Market - Farmer-to-Buyer Marketplace Platform

A full-featured, modern multi-role e-commerce platform built with Django. Farm2Market directly connects **farmers** with **buyers**, enabling streamlined product listings, cart management, order tracking, product ratings, and logistics coordination — eliminating the need for middlemen.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Tailwindcss](https://img.shields.io/badge/tailwindcss-06B6D4?logo=tailwindcss&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)


##  Features

###  Farmer
- **Registration** - Register with farm name, location, and bio
- **Farmer Dashboard** - Manage products (add, edit, view stock) from a dedicated dashboard
- **Order Management** - Receive and handle orders: confirm, reject, assign logistics, dispatch, and mark as delivered
- **Inventory Insights** - View in-stock / out-of-stock product statistics at a glance
- **Real-time Notifications** - Notification badges for new pending orders

###  Buyer
- **Registration** - Register with a delivery address
- **Product Discovery** - Browse and search products by name or category
- **Product Rating System** - Rate products (1-5 stars) after completing an order, providing valuable feedback to farmers
- **Smart Cart** - Add products to cart with support for **session-based cart** for unauthenticated users
- **Cart Merge on Login** - Anonymous cart merges seamlessly into the user account on login
- **Checkout** - Checkout groups items by farmer and creates separate per-farmer orders
- **Order History** - View past orders and real-time status updates, with a direct call-to-action to rate purchased products
- **Receipt Confirmation** - Confirm receipt to complete an order
- **Delivery Notifications** - Notification badges for delivered orders

###  Shared
- **Role-based Access Control** - Views protected per user role (farmer/buyer)
- **Notification System** - Per-user, per-order messages surfaced as navbar badges
- **Responsive UI** - Shared base template with a consistent footer across all pages
- **Admin Panel** - All models registered and manageable via Django Admin


##  Technology Stack

### Backend
- **Framework**: Django 6.0.3
- **Database**: PostgreSQL via Supabase (production) / SQLite (local development)
- **Authentication**: Django built-in authentication
- **Image Handling**: Pillow 12.2

### Frontend
- **Template Engine**: Django Templates (HTML/CSS/JS)
- **Icons & Styling**: Custom CSS with native browser styles


##  Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- PostgreSQL / Supabase account (for production database)


##  Installation

### 1. Clone the Repository
```bash
git clone <repo-url>
cd Farm2Market
```

### 2. Create Virtual Environment
```bash
py -m venv my_env
# On Windows
my_env\Scripts\activate
# On macOS/Linux
source my_env/bin/activate
```

### 3. Install Dependencies

Navigate to the directory containing `manage.py`:

```bash
cd Farm2Market
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the example file and fill in your values:

```bash
copy .env.example .env
```

Edit `.env` with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database (leave unset to use local SQLite)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Supabase S3 Media Storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=media
AWS_S3_ENDPOINT_URL=https://your-project.supabase.co/storage/v1/s3
AWS_S3_REGION_NAME=ap-southeast-1
```

> **Tip:** Leave `DATABASE_URL` unset to use a local SQLite database for development.

### 5. Configure Media Storage (Supabase S3)

Farm2Market uses **Supabase Storage (S3)** to handle user-uploaded product images.
- Create a **Public** bucket named `media` in your Supabase project.
- Inside the bucket, create a folder named `product_images`.
- Add your S3 Connection details to the `.env` file as shown above.

### 6. Database Migration
```bash
# First-time or after model changes:
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. (Optional) Seed Admin Data

Visit `http://127.0.0.1:8000/admin/` to:
- Add product `Category` entries (Vegetables, Fruits, Grains)
- Add `Logistic` providers (Pathao, Steadfast, Uber)

### 9. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.


##  Project Structure

```bash
Farm2Market/                        ← Root repo
├── README.md
├── images/                         ← Project screenshots
├── Reports/                        ← PDF documentation
│   ├── Project_Proposal.pdf
│   ├── SRS.pdf
│   └── Project Progress Report.pdf
└── Farm2Market/                    ← Django project root
    ├── manage.py
    ├── requirements.txt
    ├── .env                        ← Local secrets (not committed)
    ├── .env.example
    ├── templates/                  ← HTML templates
    │   ├── base.html               ← Shared base layout
    │   └── F2M/
    │       ├── home.html
    │       ├── products.html
    │       ├── product_detail.html
    │       ├── cart.html
    │       ├── edit_product.html
    │       ├── farmer_dashboard.html
    │       ├── farmer_profile.html
    │       ├── buyer_dashboard.html
    │       ├── buyer_profile.html
    │       ├── login.html
    │       ├── register.html
    │       └── footer.html
    ├── f2m_app/                    ← Main application
    │   ├── models.py               ← Database models
    │   ├── views.py                ← View logic
    │   ├── urls.py                 ← URL routing
    │   ├── admin.py                ← Admin configuration
    │   ├── context_processors.py   ← Cart count & notifications
    │   └── migrations/
    └── Farm2Market/                ← Project configuration
        ├── settings.py
        ├── urls.py
        ├── wsgi.py
        └── asgi.py
```


##  Database Models

- **Profile** — Extends Django's `User` with a `role` (`farmer` or `buyer`). Farmers have `farm_name`, `farm_location`, and `bio`; buyers have a `delivery_address`.
- **Category** — Groups products into categories (e.g., Vegetables, Fruits, Grains). One-to-many with Products.
- **Product** — Listed by farmers with `name`, `price_per_unit`, `stock_quantity`, `unit`, and an optional `image`.
- **Cart / CartItem** — One persistent cart per buyer. Anonymous users get a session-based cart that merges on login.
- **Order / OrderItem** — Created per farmer on checkout with a price snapshot. Order status flow:

  ```text
  PENDING
    ├── CONFIRMED → ASSIGNED → OUT_FOR_DELIVERY → DELIVERED → COMPLETED
    ├── REJECTED  (by farmer)
    └── CANCELLED (by buyer)
  ```

- **Logistic** — Delivery providers (e.g., Pathao, Steadfast) assigned by farmers at the `CONFIRMED` stage. Stores `name` and an optional `contact_number`.
- **Notification** — Per-user, per-order messages with an `is_read` flag, surfaced as navbar badges via context processors.
- **Review** — Stores 1 to 5 star product ratings submitted by buyers. Enforces a single unique review per buyer for each product.


##  Admin Features

- **Django Admin Panel** - Full CRUD operations on all models
- **Category Management** - Create and organize product categories
- **Product Management** - Add and manage farmer products with images
- **Order Management** - View and update order statuses
- **User Management** - Manage farmer and buyer accounts
- **Logistic Management** - Add and configure delivery providers
- **Stock Control** - Monitor and update product inventory
- **Review Moderation** - Monitor product ratings and reviews


##  Security Features

- CSRF protection on all forms
- Password validation and hashing via Django's auth system
- Login-required decorators on all protected views
- Role-based access control (farmers cannot access buyer views and vice versa)
- Environment variables for sensitive configuration data
- Session security for anonymous cart management


##  Deployment

The project is optimized for deployment on platforms like **Render**, **Railway**, or **Heroku** using `WhiteNoise` for static file serving and `dj-database-url` for database management.

### Render UI Deployment Guide
1. Create a new Web Service on the Render Dashboard and link this repository.
2. Ensure you have provisioned a PostgreSQL database.
3. Configure the **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
   ```
4. Configure the **Start Command**:
   ```bash
   gunicorn Farm2Market.wsgi:application
   ```

### Environment Variables Reference

| Variable       | Required | Description                                         |
|----------------|----------|-----------------------------------------------------|
| `PYTHON_VERSION`| No      | Target Python Version (e.g., `3.11.0`)              |
| `SECRET_KEY`   | Yes      | Django secret key for cryptographic signing         |
| `DEBUG`        | No       | `True` for development, `False` for production      |
| `DATABASE_URL` | No       | PostgreSQL connection string; defaults to SQLite    |
| `AWS_ACCESS_KEY_ID` | Yes | Supabase S3 Access Key for image uploads            |
| `AWS_SECRET_ACCESS_KEY` | Yes | Supabase S3 Secret Key                          |
| `AWS_STORAGE_BUCKET_NAME`| Yes | Target S3 bucket (e.g. `media`)                |
| `AWS_S3_ENDPOINT_URL` | Yes | Supabase S3 Endpoint URL                          |

##  License

This project is licensed under the MIT License - see the LICENSE file for details.


##  Acknowledgments

- Django Framework Documentation
- Supabase for hosted PostgreSQL
- Pillow for image handling


### Note

Some earlier commits may appear under a different author name due to initial Git configuration issues. This has been resolved, and all future commits are correctly linked to my GitHub profile.
