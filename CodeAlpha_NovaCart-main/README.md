# 🛒 NovaCart - Premium Full-Stack E-Commerce Store

NovaCart is a modern, responsive, production-quality e-commerce platform built using HTML5, CSS3, and Vanilla JavaScript on the frontend, and Django (Python) on the backend. Data storage, authentication, and files are managed via Firebase Firestore, Firebase Authentication, and Firebase Storage.

The project features a premium glassmorphic UI, a dual-mode database engine (enabling out-of-the-box local JSON mock testing or live Firebase connections), dynamic catalog sorting/filtering, client-side checkout cart caches, secure orders tracking, invoice downloads, and a fully functional administration CRUD control panel.

---

## 🚀 Key Features

*   **Premium Visual Experience**: Glassmorphism overlays, soft floating shadows, rounded cards, gradient action buttons, and responsive grid layouts using the `Poppins` font.
*   **Dual Database Mode**: Seamless out-of-the-box operation via a local JSON file (`db_mock.json`) or real Firebase Firestore integration.
*   **Authentication (Firebase)**: User registration, secure login, password resets, profile updates, and active session middleware checks.
*   **Advanced Catalog Search & Filters**: Live search, category selectors, brand checklists, price sliders, and star rating criteria with dynamic pagination.
*   **Cart & Checkout Management**: Interactive cart (increment/decrement quantity, delete, save for later), promo coupons validation, tax/shipping adjustments, COD/UPI/Card payment simulation, and order ID generation.
*   **Customer Dashboard**: Profile details editor, order list history, interactive timeline tracking (Pending -> Confirmed -> Packed -> Shipped -> Delivered), order cancellation, and invoice downloads.
*   **Admin Dashboard**: Analytical metrics (Revenue, Sales, Low stock alerts), Chart.js visual sales trend lines, Products CRUD modals, Orders status select triggers, and Users manager.
*   **Bonus Systems**: AI product recommendations (item-based collaborative checks), Dark/Light theme toggles, flash sales countdown clock, and console-printed email notifications.

---

## 🛠️ Tech Stack

*   **Frontend**: HTML5, CSS3 (Vanilla design, CSS Custom Properties), Vanilla JavaScript (no framework dependencies).
*   **Backend**: Django (Python) for transactions, order routing, validation, and serving static pages.
*   **Auth & Database**: Firebase Firestore + Firebase Authentication (or local Mock database engine).

---

## 📂 Folder Structure

```
NovaCart/
├── backend/
│   ├── api/
│   │   ├── urls.py
│   │   └── views.py
│   ├── views/
│   ├── serializers/
│   ├── utils/
│   │   ├── firebase_helpers.py
│   │   └── invoice_generator.py
│   ├── db_mock.json (Generated on seed)
│   ├── manage.py
│   ├── requirements.txt
│   └── settings.py
├── frontend/
│   ├── css/
│   │   ├── style.css
│   │   └── variables.css
│   ├── js/
│   │   └── main.js
│   ├── pages/
│   │   ├── shop.html
│   │   ├── product-details.html
│   │   ├── cart.html
│   │   ├── checkout.html
│   │   ├── dashboard.html
│   │   ├── admin-dashboard.html
│   │   ├── wishlist.html
│   │   ├── about.html
│   │   └── contact.html
│   └── index.html
├── firebase/
│   ├── firebase-config.js
│   └── firebase-services.js
├── scripts/
│   └── seed_firestore.py
└── README.md
```

---

## ⚡ Setup & Installation

### 1. Clone & Set Workspace
Make sure your active IDE workspace is set to the project root directory:
```bash
C:\Users\LENOVO\.gemini\antigravity\scratch\novacart
```

### 2. Configure Python Virtual Environment
Navigate to the project folder and configure a virtual environment:
```bash
# Create venv
py -m venv venv

# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Seed Database (Mock or Real)
Before launching, seed the database with 50 products, 10 categories, 20 users, and 20 sample orders:
```bash
python scripts/seed_firestore.py
```
*(By default, this creates a local database mock file `backend/db_mock.json` which can be modified directly).*

### 5. Launch Local Server
Start the Django backend:
```bash
python backend/manage.py runserver
```
Visit the store in your browser at: `http://127.0.0.1:8000/`

---

## ☁️ Firebase Integration

To transition from the local mock engine to a live Firebase project:

1.  **Client Configuration**: Open `firebase/firebase-config.js` and replace the placeholder credential strings inside `firebaseConfig` with your Firebase web configuration credentials.
2.  **Admin SDK Key**: Generate a new private key certificate JSON from your Firebase Project Settings -> Service Accounts, download it, and save it locally.
3.  **Environment Variables**: Create a `.env` file inside the `backend/` folder:
    ```env
    FIREBASE_MOCK_MODE=False
    FIREBASE_SERVICE_ACCOUNT_PATH="C:/path/to/your/firebase-service-account.json"
    DJANGO_DEBUG=True
    ```
4.  **Re-seed**: Run `python scripts/seed_firestore.py` to push the 50 products and data collections to your live Firestore database instead of the local file.
