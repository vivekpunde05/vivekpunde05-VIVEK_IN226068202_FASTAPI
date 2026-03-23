# 🎬 CineStar — Movie Ticket Booking API

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)

A FastAPI backend for a Movie Ticket Booking System — Final Project for FastAPI Internship Training (Days 1–6).

---

## � Quick Start

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open Swagger UI: `http://127.0.0.1:8000/docs`

---

## 🎯 Features

- Browse, search, filter, sort & paginate movies
- Book tickets with seat type (standard / premium / recliner)
- Apply promo codes: `SAVE10` (10% off), `SAVE20` (20% off)
- Seat hold → confirm or release workflow
- Full CRUD for movies (add, update, delete)

---

## 📌 Key Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/movies` | List all movies |
| GET | `/movies/browse` | Search + filter + sort + paginate |
| POST | `/bookings` | Create a booking |
| POST | `/seat-hold` | Hold seats temporarily |
| POST | `/seat-confirm/{id}` | Confirm hold → booking |
| DELETE | `/seat-release/{id}` | Release hold |
| POST | `/movies` | Add new movie |
| PUT | `/movies/{id}` | Update movie |
| DELETE | `/movies/{id}` | Delete movie |

---

## 📦 Dependencies

```
fastapi
uvicorn
pydantic
```

---

**Tech Stack:** Python · FastAPI · Pydantic · Uvicorn
