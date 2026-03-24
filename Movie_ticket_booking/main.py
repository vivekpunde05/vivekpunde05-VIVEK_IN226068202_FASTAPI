from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI(title="CineStar Booking", description="Movie Ticket Booking System")

#  IN-MEMORY DATA STORE
movies = [
    {"id": 1, "title": "Inception", "genre": "Action", "language": "English",
     "duration_mins": 148, "ticket_price": 250, "seats_available": 80},
    {"id": 2, "title": "The Dark Knight", "genre": "Action", "language": "English",
     "duration_mins": 152, "ticket_price": 300, "seats_available": 60},
    {"id": 3, "title": "Kal Ho Naa Ho", "genre": "Drama", "language": "Hindi",
     "duration_mins": 186, "ticket_price": 150, "seats_available": 100},
    {"id": 4, "title": "Munnabhai MBBS", "genre": "Comedy", "language": "Hindi",
     "duration_mins": 156, "ticket_price": 120, "seats_available": 120},
    {"id": 5, "title": "Conjuring", "genre": "Horror", "language": "English",
     "duration_mins": 112, "ticket_price": 200, "seats_available": 50},
    {"id": 6, "title": "3 Idiots", "genre": "Comedy", "language": "Hindi",
     "duration_mins": 170, "ticket_price": 130, "seats_available": 90},
    {"id": 7, "title": "RRR", "genre": "Action", "language": "Telugu",
     "duration_mins": 187, "ticket_price": 180, "seats_available": 70},
    {"id": 8, "title": "Tumbbad", "genre": "Horror", "language": "Hindi",
     "duration_mins": 104, "ticket_price": 160, "seats_available": 40},
]

movie_counter = 9

bookings = []
booking_counter = 1

holds = []
hold_counter = 1

#  PYDANTIC MODELS

class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)
    phone: str = Field(..., min_length=10)
    seat_type: str = Field(default="standard")
    promo_code: str = Field(default="")

class NewMovie(BaseModel):
    title: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    language: str = Field(..., min_length=2)
    duration_mins: int = Field(..., gt=0)
    ticket_price: int = Field(..., gt=0)
    seats_available: int = Field(..., gt=0)

class SeatHoldRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)

# ─────────────────────────────────────────────
#  HELPER FUNCTIONS  

def find_movie(movie_id: int):
    """Return the movie dict or None."""
    for m in movies:
        if m["id"] == movie_id:
            return m
    return None


def calculate_ticket_cost(base_price: int, seats: int, seat_type: str, promo_code: str = ""):
    """
    seat_type multipliers:
        standard  → 1×
        premium   → 1.5×
        recliner  → 2×
    promo_codes:
        SAVE10 → 10 % off
        SAVE20 → 20 % off
    Returns original_cost and discounted_cost.
    """
    multipliers = {"standard": 1.0, "premium": 1.5, "recliner": 2.0}
    multiplier = multipliers.get(seat_type.lower(), 1.0)
    original_cost = base_price * seats * multiplier

    discount = 0.0
    if promo_code.upper() == "SAVE10":
        discount = 0.10
    elif promo_code.upper() == "SAVE20":
        discount = 0.20

    discounted_cost = original_cost * (1 - discount)
    return round(original_cost, 2), round(discounted_cost, 2)


def filter_movies_logic(
    genre: Optional[str],
    language: Optional[str],
    max_price: Optional[int],
    min_seats: Optional[int],
):
    """Apply optional filters with is-not-None checks."""
    result = movies[:]
    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]
    if language is not None:
        result = [m for m in result if m["language"].lower() == language.lower()]
    if max_price is not None:
        result = [m for m in result if m["ticket_price"] <= max_price]
    if min_seats is not None:
        result = [m for m in result if m["seats_available"] >= min_seats]
    return result



#  Q1  —  Home Route

@app.get("/")
def home():
    return {"message": "Welcome to CineStar Booking"}

#  Q5  —  Summary
#
@app.get("/movies/summary")
def movies_summary():
    if not movies:
        return {"total_movies": 0}

    prices = [m["ticket_price"] for m in movies]
    genre_count = {}
    for m in movies:
        genre_count[m["genre"]] = genre_count.get(m["genre"], 0) + 1

    return {
        "total_movies": len(movies),
        "most_expensive_ticket": max(prices),
        "cheapest_ticket": min(prices),
        "total_seats_across_all_movies": sum(m["seats_available"] for m in movies),
        "movies_by_genre": genre_count,
    }


# ═════════════════════════════════════════════
#  Q10  —  Filter  (FIXED route)
# ═════════════════════════════════════════════

@app.get("/movies/filter")
def filter_movies(
    genre: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    max_price: Optional[int] = Query(default=None),
    min_seats: Optional[int] = Query(default=None),
):
    result = filter_movies_logic(genre, language, max_price, min_seats)
    return {"total": len(result), "movies": result}


# ═════════════════════════════════════════════
#  Q16  —  Search  (FIXED route)
# ═════════════════════════════════════════════

@app.get("/movies/search")
def search_movies(keyword: str = Query(...)):
    kw = keyword.lower()
    result = [
        m for m in movies
        if kw in m["title"].lower()
        or kw in m["genre"].lower()
        or kw in m["language"].lower()
    ]
    if not result:
        return {"message": f"No movies found matching '{keyword}'", "total_found": 0}
    return {"total_found": len(result), "movies": result}


# ═════════════════════════════════════════════
#  Q17  —  Sort  (FIXED route)
# ═════════════════════════════════════════════

@app.get("/movies/sort")
def sort_movies(
    sort_by: str = Query(default="ticket_price",
                         description="ticket_price | title | duration_mins | seats_available"),
    order: str = Query(default="asc", description="asc | desc"),
):
    valid_sort_fields = {"ticket_price", "title", "duration_mins", "seats_available"}
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort_fields}")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")

    reverse = order == "desc"
    sorted_movies = sorted(movies, key=lambda m: m[sort_by], reverse=reverse)
    return {"sort_by": sort_by, "order": order, "movies": sorted_movies}


# ═════════════════════════════════════════════
#  Q18  —  Pagination  (FIXED route)
# ═════════════════════════════════════════════

@app.get("/movies/page")
def paginate_movies(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=3, ge=1),
):
    total = len(movies)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    end = start + limit
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "movies": movies[start:end],
    }


# ═════════════════════════════════════════════
#  Q20  —  Combined Browse  (FIXED route)
# ═════════════════════════════════════════════

@app.get("/movies/browse")
def browse_movies(
    keyword: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    language: Optional[str] = Query(default=None),
    sort_by: str = Query(default="ticket_price",
                         description="ticket_price | title | duration_mins | seats_available"),
    order: str = Query(default="asc", description="asc | desc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=3, ge=1),
):
    valid_sort_fields = {"ticket_price", "title", "duration_mins", "seats_available"}
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort_fields}")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")

    # Step 1 — keyword filter
    result = movies[:]
    if keyword is not None:
        kw = keyword.lower()
        result = [
            m for m in result
            if kw in m["title"].lower()
            or kw in m["genre"].lower()
            or kw in m["language"].lower()
        ]

    # Step 2 — genre / language filter
    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]
    if language is not None:
        result = [m for m in result if m["language"].lower() == language.lower()]

    # Step 3 — sort
    reverse = order == "desc"
    result = sorted(result, key=lambda m: m[sort_by], reverse=reverse)

    # Step 4 — paginate
    total = len(result)
    total_pages = math.ceil(total / limit) if total else 1
    start = (page - 1) * limit
    end = start + limit

    return {
        "keyword": keyword,
        "genre": genre,
        "language": language,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "movies": result[start:end],
    }


# ═════════════════════════════════════════════
#  Q2  —  GET all movies  (FIXED route)
# ═════════════════════════════════════════════

@app.get("/movies")
def get_all_movies():
    return {
        "total": len(movies),
        "total_seats_available": sum(m["seats_available"] for m in movies),
        "movies": movies,
    }


# ═════════════════════════════════════════════
#  Q11  —  POST /movies  (Create new movie)
# ═════════════════════════════════════════════

@app.post("/movies", status_code=201)
def add_movie(movie: NewMovie):
    global movie_counter
    # Duplicate title check
    for m in movies:
        if m["title"].lower() == movie.title.lower():
            raise HTTPException(status_code=400, detail="A movie with this title already exists")

    new_movie = {
        "id": movie_counter,
        **movie.dict(),
    }
    movie_counter += 1
    movies.append(new_movie)
    return {"message": "Movie added successfully", "movie": new_movie}


# ═════════════════════════════════════════════
#  Q3  —  GET /movies/{movie_id}  (VARIABLE route — last)
# ═════════════════════════════════════════════

@app.get("/movies/{movie_id}")
def get_movie_by_id(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id {movie_id} not found")
    return movie


# ═════════════════════════════════════════════
#  Q12  —  PUT /movies/{movie_id}
# ═════════════════════════════════════════════

@app.put("/movies/{movie_id}")
def update_movie(
    movie_id: int,
    ticket_price: Optional[int] = Query(default=None),
    seats_available: Optional[int] = Query(default=None),
):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id {movie_id} not found")

    if ticket_price is not None:
        movie["ticket_price"] = ticket_price
    if seats_available is not None:
        movie["seats_available"] = seats_available

    return {"message": "Movie updated successfully", "movie": movie}


# ═════════════════════════════════════════════
#  Q13  —  DELETE /movies/{movie_id}
# ═════════════════════════════════════════════

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id {movie_id} not found")

    # Business rule: cannot delete if bookings exist for this movie
    has_bookings = any(b["movie_id"] == movie_id for b in bookings)
    if has_bookings:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete movie — existing bookings found for this movie",
        )

    movies.remove(movie)
    return {"message": f"Movie '{movie['title']}' deleted successfully"}


#  BOOKINGS

# ═════════════════════════════════════════════
#  Q19  —  Bookings Search / Sort / Page  (FIXED routes first)
# ═════════════════════════════════════════════

@app.get("/bookings/search")
def search_bookings(customer_name: str = Query(...)):
    name = customer_name.lower()
    result = [b for b in bookings if name in b["customer_name"].lower()]
    if not result:
        return {"message": f"No bookings found for '{customer_name}'", "total": 0}
    return {"total": len(result), "bookings": result}


@app.get("/bookings/sort")
def sort_bookings(
    sort_by: str = Query(default="total_cost", description="total_cost | seats"),
    order: str = Query(default="asc", description="asc | desc"),
):
    valid_fields = {"total_cost", "seats"}
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_fields}")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    reverse = order == "desc"
    sorted_b = sorted(bookings, key=lambda b: b[sort_by], reverse=reverse)
    return {"sort_by": sort_by, "order": order, "bookings": sorted_b}


@app.get("/bookings/page")
def paginate_bookings(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=3, ge=1),
):
    total = len(bookings)
    total_pages = math.ceil(total / limit) if total else 1
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "bookings": bookings[start: start + limit],
    }


# ═════════════════════════════════════════════
#  Q4  —  GET /bookings  (list all)
# ═════════════════════════════════════════════

@app.get("/bookings")
def get_all_bookings():
    total_revenue = sum(b["total_cost"] for b in bookings)
    return {
        "total": len(bookings),
        "total_revenue": round(total_revenue, 2),
        "bookings": bookings,
    }


# ═════════════════════════════════════════════
#  Q8 + Q9  —  POST /bookings  (Create booking)
# ═════════════════════════════════════════════

@app.post("/bookings", status_code=201)
def create_booking(request: BookingRequest):
    global booking_counter

    # Check movie exists
    movie = find_movie(request.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id {request.movie_id} not found")

    # Check seats availability
    if movie["seats_available"] < request.seats:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough seats. Available: {movie['seats_available']}, Requested: {request.seats}",
        )

    # Calculate cost with promo
    original_cost, discounted_cost = calculate_ticket_cost(
        movie["ticket_price"],
        request.seats,
        request.seat_type,
        request.promo_code,
    )

    # Reduce available seats
    movie["seats_available"] -= request.seats

    booking = {
        "booking_id": booking_counter,
        "customer_name": request.customer_name,
        "movie_id": request.movie_id,
        "movie_title": movie["title"],
        "seats": request.seats,
        "seat_type": request.seat_type,
        "phone": request.phone,
        "promo_code": request.promo_code,
        "original_cost": original_cost,
        "total_cost": discounted_cost,
    }
    bookings.append(booking)
    booking_counter += 1

    return {"message": "Booking confirmed!", "booking": booking}


#  SEAT-HOLD WORKFLOW 

#  Q14  —  POST /seat-hold  |  GET /seat-hold
# ═════════════════════════════════════════════

@app.get("/seat-hold")
def get_all_holds():
    return {"total_holds": len(holds), "holds": holds}


@app.post("/seat-hold", status_code=201)
def create_seat_hold(request: SeatHoldRequest):
    global hold_counter

    movie = find_movie(request.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id {request.movie_id} not found")

    if movie["seats_available"] < request.seats:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough seats to hold. Available: {movie['seats_available']}",
        )

    # Temporarily reduce seats
    movie["seats_available"] -= request.seats

    hold = {
        "hold_id": hold_counter,
        "customer_name": request.customer_name,
        "movie_id": request.movie_id,
        "movie_title": movie["title"],
        "seats": request.seats,
        "status": "on_hold",
    }
    holds.append(hold)
    hold_counter += 1

    return {"message": "Seats held successfully!", "hold": hold}

#  Q15  —  POST /seat-confirm/{hold_id}  |  DELETE /seat-release/{hold_id}
# ═════════════════════════════════════════════

@app.post("/seat-confirm/{hold_id}", status_code=201)
def confirm_seat_hold(hold_id: int):
    global booking_counter

    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold:
        raise HTTPException(status_code=404, detail=f"Hold with id {hold_id} not found")

    movie = find_movie(hold["movie_id"])
    if not movie:
        raise HTTPException(status_code=404, detail="Movie for this hold no longer exists")

    # Convert hold → confirmed booking
    booking = {
        "booking_id": booking_counter,
        "customer_name": hold["customer_name"],
        "movie_id": hold["movie_id"],
        "movie_title": hold["movie_title"],
        "seats": hold["seats"],
        "seat_type": "standard",
        "phone": "N/A (hold-converted)",
        "promo_code": "",
        "original_cost": movie["ticket_price"] * hold["seats"],
        "total_cost": movie["ticket_price"] * hold["seats"],
    }
    bookings.append(booking)
    booking_counter += 1

    # Remove from holds
    holds.remove(hold)
    return {
        "message": "Hold confirmed! Booking created.",
        "booking": booking,
    }

@app.delete("/seat-release/{hold_id}")
def release_seat_hold(hold_id: int):
    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold:
        raise HTTPException(status_code=404, detail=f"Hold with id {hold_id} not found")

    # Return seats to movie
    movie = find_movie(hold["movie_id"])
    if movie:
        movie["seats_available"] += hold["seats"]

    holds.remove(hold)
    return {
        "message": f"Hold {hold_id} released. {hold['seats']} seat(s) returned to '{hold['movie_title']}'.",
    }
