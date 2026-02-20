# 🎬 Media Review System

A command-line application built in Python that lets users register, log in, browse media (movies, web shows, songs), submit reviews, get personalized recommendations, and subscribe to review notifications. The project is designed to demonstrate several real-world software engineering patterns including the **Factory Pattern**, **Observer Pattern**, **Async Processing**, **Caching with Fallback**, and **Token-Based Authentication**.

---

## 📁 Project Structure

```
media-review/
├── app/
│   ├── __init__.py
│   ├── db.py                  # SQLAlchemy engine & session setup
│   ├── models.py              # All ORM models (User, Media, Review, Session, etc.)
│   └── cache.py               # Redis cache with in-memory fallback
│
├── services/
│   ├── auth_service.py        # Register, login, logout, token validation
│   ├── media_service.py       # List, search, add, top-rated media
│   ├── media_factory.py       # Factory Pattern — creates Movie, WebShow, Song objects
│   ├── review_service.py      # Add review, view reviews, bulk async reviews
│   ├── review_summary_service.py  # Updates review summary aggregate table
│   ├── async_review_queue.py  # Queue reviews for concurrent processing
│   ├── bulk_logger.py         # Structured JSON logging for bulk operations
│   ├── notification_service.py    # Observer Pattern — subscribe & notify
│   ├── recommender.py         # Collaborative filtering recommendations
│   ├── review_analytics.py    # Sentiment analysis and keyword stats
│   ├── rebuild_summary.py     # Rebuild materialized view tables
│   ├── similarity.py          # Cosine similarity for user taste comparison
│   ├── taste_profile.py       # Builds & stores per-user genre taste weights
│   └── user_profile.py        # Computes genre→average-rating profile dict
│
├── tests/
│   ├── test_auth.py           # Auth unit tests (in-memory DB)
│   ├── test_review_service.py # Review + similarity + cache unit tests
│   └── test_media_factory.py  # Factory Pattern unit tests
│
├── media_review.py            # Main CLI entry point
├── init_db.py                 # Create all database tables
├── seed_data.py               # Seed database with sample data
├── reviews.csv                # Sample CSV file for bulk review import
├── requirements.txt           # Python dependencies
└── logs/
    └── bulk_reviews.log       # Auto-created log for bulk operations
```

---

## 🗃️ Database Schema

The project uses **SQLite** via **SQLAlchemy ORM**. The database file is `media.db`, created in the working directory.

### Tables and Their Purpose

| Table | Purpose |
|-------|---------|
| `users` | Stores registered users (id, username, hashed password) |
| `sessions` | Stores login tokens with expiry timestamps |
| `media` | Stores movies, web shows, and songs |
| `reviews` | Stores user reviews linked to media |
| `rating_summary` | Materialized view — precomputed avg rating per media |
| `review_summaries` | Secondary materialized view (same structure as rating_summary) |
| `user_taste` | Genre-level rating weights per user (used for recommendations) |
| `subscriptions` | Tracks which users subscribed to notifications for which media |

### Why Two Summary Tables?

`rating_summary` and `review_summaries` store the same kind of aggregate (avg rating + count) but serve different purposes. `rating_summary` is updated live on every new review. `review_summaries` can be bulk-rebuilt via `--rebuild-summaries`. This separation allows the live path to stay fast while the rebuild path can recalculate everything from scratch safely.

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone or extract the project
cd media-review

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database (creates media.db and all tables)
python init_db.py

# 5. (Optional) Seed sample data
python seed_data.py
```

### requirements.txt

```
sqlalchemy>=2.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
redis
faker
```

| Package | Why It's Used |
|---------|--------------|
| `sqlalchemy` | ORM for database access — maps Python classes to SQL tables |
| `passlib[bcrypt]` | Password hashing using the bcrypt algorithm |
| `bcrypt` | C-extension backend for bcrypt (fast hashing) |
| `redis` | Optional Redis client — used if Redis is running; otherwise the app falls back to in-memory cache automatically |
| `faker` | Used in seed_data.py to generate realistic fake media/review data |

---

## 🚀 How to Use — All CLI Commands

### Authentication

```bash
# Register a new account
python media_review.py --register alice secret123

# Log in — prints your session token
python media_review.py --login alice secret123

# Log out — invalidates the token
python media_review.py --logout
```

After `--login`, you will see a token printed. **Copy this token** — you need to pass it with every review command using `--token <your-token>`.

Tokens expire after **30 minutes**. After expiry, log in again to get a new token.

---

### Browsing Media (No Login Required)

```bash
# List all media in the database
python media_review.py --list

# Search media by title (partial match, case-insensitive)
python media_review.py --search "inception"

# Show top 5 rated media (based on RatingSummary table)
python media_review.py --top-rated

# Get personalized recommendations for user with ID 1
python media_review.py --recommend 1

# View all reviews for a specific media ID
python media_review.py --view-reviews 3

# View sentiment analysis and keyword stats for a media
python media_review.py --insights 3
```

---

### Writing Reviews (Requires --token)

```bash
# Add a single review
python media_review.py --review <media_id> <rating_1_to_5> "Your comment" --token <your-token>

# Example
python media_review.py --review 2 4 "Really enjoyed this one" --token abc123

# Bulk import reviews from a CSV file
python media_review.py --bulk-review reviews.csv --token <your-token>

# View the bulk import log
python media_review.py --view-bulk-log
```

**CSV format for bulk reviews:**
```csv
media_id,rating,comment
1,5,"Amazing film"
2,3,"It was okay"
3,4,"Great music"
```

---

### Queue-Based Concurrent Reviews

This feature lets you queue up multiple reviews and then process them all concurrently.

```bash
# Queue individual reviews (up to --review10)
python media_review.py --review1 1 5 "Masterpiece" --token <token>
python media_review.py --review2 2 4 "Good film" --token <token>
python media_review.py --review3 3 3 "Average" --token <token>

# Check what's in the queue
python media_review.py --queue-status

# Process all queued reviews concurrently
python media_review.py --process-queue --token <token>
```

Queue state is saved in `review_queue.jsonl`. Each job has a status: `pending`, `done`, `skipped`, or `failed`.

---

### Notifications & Subscriptions (Requires Login via .session)

```bash
# Subscribe to a media and see its recent reviews
python media_review.py --notification 1

# See all recent reviews for all your subscribed media
python media_review.py --my-notifications
```

---

### Admin Commands (Requires Login via .session)

```bash
# Add a new media entry
python media_review.py --add-media "Dune" "movie" "Sci-Fi" 2021

# Rebuild rating summary tables from scratch
python media_review.py --rebuild-summaries
```

---

## 🔒 Authentication — How It Works

There are **two authentication modes** in this system:

### Mode 1: Token-based (--token flag)
Used for all review/write operations. This is the explicit security gate.

1. User logs in → a UUID token is generated and stored in the `sessions` table with a 30-minute expiry.
2. Token is also written to a local `.session` file.
3. To perform a review, user must pass `--token <token>` explicitly.
4. The `_require_token()` function in `media_review.py` calls `validate_token_arg()` from `auth_service.py`, which checks the token against the DB.
5. If the token has expired, it is deleted from the DB and the user is told to log in again.

### Mode 2: Session file (implicit)
Used for softer actions like adding media, subscribing to notifications.

1. `_require_login()` reads the `.session` file.
2. Calls `validate_session()` → `_validate_token()` internally.
3. Returns the user_id or exits with a helpful error.

### Password Hashing
Passwords are hashed using **bcrypt** via `passlib`. The plain-text password is never stored. On login, `pwd.verify(password, hash)` is used to compare.

```python
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
user = User(username=username, password_hash=pwd.hash(password))
```

---

## 🏭 Design Pattern 1: Factory Pattern

**File:** `services/media_factory.py`

The Factory Pattern is used to create different types of media objects (Movie, WebShow, Song) without the caller needing to know which class to instantiate. The caller just provides a `media_type` string.

### Class Hierarchy

```
Media (base)
├── Movie     → has extra field: rating
├── WebShow   → has extra field: episodes
└── Song      → has extra field: popularity
```

### How It Works

```python
class MediaFactory:
    @staticmethod
    def create_media(media_type, media_id, title, genre, **kwargs):
        if media_type.lower() == 'movie':
            return Movie(media_id, title, genre, kwargs.get('rating'))
        elif media_type.lower() == 'webshow':
            return WebShow(media_id, title, genre, kwargs.get('episodes', 0))
        elif media_type.lower() == 'song':
            return Song(media_id, title, genre, kwargs.get('popularity', 0))
        else:
            raise ValueError(f"Unknown media type: {media_type}")
```

**Why this is useful:** If you add a new media type like `Podcast` in the future, you only change `MediaFactory.create_media()` — not every place in your codebase that creates media objects.

The type is also **case-insensitive** — `"MOVIE"`, `"Movie"`, and `"movie"` all work.

---

## 👀 Design Pattern 2: Observer Pattern

**File:** `services/notification_service.py`

The Observer Pattern allows users (observers) to subscribe to a media item (subject) and get notified when a new review is posted.

### How It Works

1. A user calls `--notification <media_id>` → `subscribe()` is called → a `Subscription` row is inserted in the DB.
2. Every time `add_review()` runs successfully, it calls `notify_subscribers(db, media_id, message)`.
3. `notify_subscribers` queries all subscriptions for that `media_id` and prints a notification line for each subscriber.

```python
def notify_subscribers(db, media_id, message):
    subs = db.query(Subscription).filter_by(media_id=media_id).all()
    for sub in subs:
        print(f"  Notification -> User {sub.user_id}: {message}")
```

**Key Design Decision:** Subscriptions are stored in the database (not in memory). This means subscriptions **persist across CLI sessions** — you subscribe once and keep receiving notifications in future runs.

---

## ⚡ Async Processing — Bulk Reviews

**File:** `services/review_service.py` and `services/async_review_queue.py`

### Bulk CSV Reviews (`--bulk-review`)

When you run `--bulk-review reviews.csv`, the system does the following:

1. Reads all rows from the CSV.
2. Splits them into **batches of 50**.
3. For each batch, creates an `asyncio` task for every row.
4. Uses `asyncio.gather()` to run all tasks in the batch concurrently.
5. Each task offloads the actual DB write to a `ThreadPoolExecutor` (because SQLite is blocking I/O).
6. Progress is printed after each batch.
7. After all batches, `rebuild_user_summary()` is called **once** (not per-review) for efficiency.

```python
# Simplified flow
for batch in batches:
    tasks = [_one_task(user_id, media_id, rating, comment, row_num) for row in batch]
    results = await asyncio.gather(*tasks)
```

The flag `skip_taste_rebuild=True` is passed to `add_review()` during bulk processing. This prevents the expensive taste-profile rebuild from running 100+ times — it's rebuilt just once at the end.

### Queued Reviews (`--review1` to `--review10` + `--process-queue`)

This is a **fire-and-forget queue system**:

1. `--review1` through `--review10` write job entries to `review_queue.jsonl` instantly and return.
2. The queue file stores JSON lines with fields: `job_id`, `user_id`, `media_id`, `rating`, `comment`, `status`, `queued_at`.
3. `--process-queue` reads all `pending` jobs and processes them concurrently using `asyncio` with a semaphore to cap concurrency at 5 parallel jobs at a time.
4. Each job's status is updated to `done`, `skipped`, or `failed` in the queue file.

```python
sem = asyncio.Semaphore(5)
await asyncio.gather(*[_process_one(j, sem) for j in jobs])
```

A **threading lock** (`threading.Lock()`) protects the queue file from race conditions when multiple threads try to update the same line simultaneously.

---

## 💾 Caching — Redis with In-Memory Fallback

**File:** `app/cache.py`

The cache layer is designed to work **with or without Redis** running.

### How It Works

On startup, `cache.py` tries to connect to Redis:
```python
_client.ping()
REDIS_AVAILABLE = True
```

If the ping fails (Redis not running), it silently falls back to an in-memory dictionary. **The rest of the app doesn't need to change at all** — it just calls `cache_get()`, `cache_set()`, `cache_delete()`.

### What Gets Cached

| Cache Key | Content | TTL |
|-----------|---------|-----|
| `media:list` | Full media list | 300s |
| `media:search:<query>` | Search results | 120s |
| `media:top_rated:<limit>` | Top rated media | 60s |
| `reviews:<media_id>` | Reviews + stats for one media | 300s |
| `recommend:<user_id>` | Recommendations for a user | 300s |

### Cache Invalidation

Whenever a new review is added, the relevant cache keys are deleted:
```python
cache_delete(f"reviews:{media_id}")
cache_delete_pattern("media:top_rated:*")
cache_delete("media:list")
cache_delete(f"recommend:{user_id}")
```

`cache_delete_pattern` uses Redis `SCAN` in Redis mode, or a prefix-match loop in memory-fallback mode.

---

## 🤖 Recommendation System

**Files:** `services/recommender.py`, `services/user_profile.py`, `services/similarity.py`, `services/taste_profile.py`

This implements **collaborative filtering** — recommending content based on what similar users liked.

### Process Flow

```
Step 1: Build the target user's taste profile
        → {genre: avg_rating}  e.g. {"Action": 4.5, "Drama": 3.0}

Step 2: Build taste profiles for all other users

Step 3: Compute cosine similarity between target and each other user
        → Score between 0 (no overlap) and 1 (identical tastes)

Step 4: Pick top 3 most similar users

Step 5: Find media that similar users rated ≥ 4, not yet seen by target user

Step 6: Rank by how many similar users recommended it

Step 7: Return top 5
```

### Cosine Similarity

```python
def cosine_similarity(p1, p2):
    common = set(p1.keys()) & set(p2.keys())
    dot    = sum(p1[g] * p2[g] for g in common)
    mag1   = math.sqrt(sum(v*v for v in p1.values()))
    mag2   = math.sqrt(sum(v*v for v in p2.values()))
    return dot / (mag1 * mag2)
```

Two users who love Action (5/5) and hate Drama (1/5) will get a similarity score close to 1.0. A user who loves Action but has never rated anything the other user has rated gets 0.

### Taste Profile Storage

Each time a user adds a review, `rebuild_user_summary(user_id)` updates the `user_taste` table:
```
user_id | genre   | weight
1       | Action  | 4.5
1       | Drama   | 3.0
```

This is used as a persistent cache for the recommendation engine.

### Fallback

If a user has no reviews (no taste profile), the system falls back to showing the top-rated media instead.

---

## 📊 Review Analytics (`--insights`)

**File:** `services/review_analytics.py`

Provides a quick analysis of reviews for a given media:

- **Average rating** from the DB
- **Positive sentiment count** — reviews containing words like `good`, `great`, `amazing`, `masterpiece`, `excellent`, `love`, `best`
- **Negative sentiment count** — reviews containing `bad`, `boring`, `waste`, `poor`, `slow`, `worst`
- **Top 5 keywords** — most frequent words (4+ characters) extracted from all review comments using regex + `Counter`

This is a simple keyword-based sentiment analysis (not ML-based), but it works well for quick summary stats.

---

## 📋 Bulk Logging

**File:** `services/bulk_logger.py`

Every bulk review operation writes structured JSON lines to `logs/bulk_reviews.log`. Each line is one event:

| Event | Logged When |
|-------|-------------|
| `BULK_START` | Bulk operation begins |
| `SUCCESS` | A review row was added successfully |
| `SKIP` | Review was skipped (duplicate) |
| `FAIL` | Review failed (bad data or error) |
| `BULK_DONE` | Bulk operation complete with summary stats |

```json
{"event": "BULK_START", "file": "reviews.csv", "total": 100, "user_id": 1, "ts": "..."}
{"event": "SUCCESS", "row": 1, "user_id": 1, "media_id": 3, "rating": 5, "comment": "Great!", "ts": "..."}
{"event": "BULK_DONE", "total": 100, "success": 95, "skipped": 4, "failed": 1, "elapsed_sec": 2.3, "ts": "..."}
```

View this log with:
```bash
python media_review.py --view-bulk-log
```

---

## 🧪 Tests

**Location:** `tests/`

Tests use Python's built-in `unittest` module with **in-memory SQLite** so nothing is written to `media.db` during testing.

### Running Tests

```bash
python -m pytest tests/
# or
python -m unittest discover tests/
```

### What's Tested

**`test_auth.py`** — Auth Service
- Register a new user → user appears in DB
- Register duplicate → only one user created
- Login with correct password → token returned
- Login with wrong password → `None` returned
- `.session` file created on login

**`test_review_service.py`** — Review Service + Similarity + Cache
- Add review → appears in DB
- Duplicate review → blocked (one review per user per media)
- Invalid rating (e.g., 10/5) → rejected
- Media not found → rejected
- Cosine similarity: identical profiles → score = 1.0
- Cosine similarity: no common genres → score = 0
- Cache set/get/delete/TTL expiry

**`test_media_factory.py`** — Factory Pattern
- `create_media("movie", ...)` → returns `Movie` instance
- `create_media("webshow", ...)` → returns `WebShow` instance with correct episode count
- `create_media("song", ...)` → returns `Song` instance with correct popularity
- Invalid type raises `ValueError`
- `display_info()` includes the title
- Default values (0 episodes, 0 popularity) work correctly
- Case-insensitive type matching (`"MOVIE"` works)

---

## 🔄 Full Process Flow — Submitting a Review

Here is the end-to-end flow when a user runs:
```bash
python media_review.py --review 2 5 "Loved it" --token abc-123
```

```
1. argparse parses --review, --token
2. _require_token() is called
   → checks args.token is present
   → calls validate_token_arg("abc-123")
   → queries sessions table for token
   → checks expiry datetime
   → returns user_id (e.g. 1)

3. SessionLocal() opens a DB connection

4. add_review(db, user_id=1, media_id=2, rating=5, comment="Loved it") is called

5. Validate rating is 1–5 ✅
6. Query media table — confirm media ID 2 exists ✅
7. Check reviews table — no duplicate for (user_id=1, media_id=2) ✅
8. Insert new Review row into DB
9. db.commit()

10. update_review_summary(db, media_id=2)
    → recalculate avg + count for media 2
    → update review_summaries table

11. _update_rating_summary(db, media_id=2)
    → recalculate avg + count
    → upsert rating_summary table

12. rebuild_user_summary(user_id=1)
    → query all reviews by user 1 joined with media genre
    → compute avg rating per genre
    → delete old user_taste rows for user 1
    → insert new user_taste rows

13. Invalidate cache keys:
    → delete reviews:2
    → delete media:top_rated:* (pattern)
    → delete media:list
    → delete recommend:1

14. Print "Review Added" to console

15. notify_subscribers(db, media_id=2, message="New review...")
    → query subscriptions for media_id=2
    → print notification for each subscriber

16. db.close()
```

---

## 🔄 Full Process Flow — Bulk Review

```bash
python media_review.py --bulk-review reviews.csv --token abc-123
```

```
1. Token validated → user_id obtained
2. CSV file opened → rows loaded into list
3. log_bulk_start() writes BULK_START event to log file
4. Rows split into batches of 50
5. For each batch:
   a. For each row, create async task _one_task(...)
   b. asyncio.gather(*tasks) runs all tasks concurrently
      → Each task runs add_review() in a ThreadPoolExecutor
      → Results: "success", "skip", or "fail"
      → Logged to bulk_reviews.log
   c. Progress line printed: "Progress: 50/200 (25%) Added: 45 Skipped: 5 Failed: 0"
6. After all batches: rebuild_user_summary(user_id) called once
7. log_bulk_done() writes BULK_DONE summary
8. Final summary printed to console
```

---

## ❓ Common Interview Questions & Answers

**Q: Why use `asyncio` with a `ThreadPoolExecutor` for DB writes?**

`asyncio` is single-threaded and cannot do blocking I/O natively. SQLite calls are blocking. So we use `run_in_executor` to offload each DB write to a thread pool, while `asyncio.gather` coordinates them. This gives us true concurrency for I/O-bound operations without rewriting everything in threads.

**Q: Why is there a semaphore in `async_review_queue.py`?**

The semaphore `asyncio.Semaphore(5)` limits how many queue jobs run simultaneously. Without it, 100 pending jobs would all try to open DB connections at once, which can overwhelm SQLite. The semaphore is a flow-control mechanism.

**Q: Why does `add_review` have a `skip_taste_rebuild` flag?**

`rebuild_user_summary()` recalculates genre taste from all of a user's reviews — it's a DB read+write. Calling it for every row in a 200-row CSV would be 200 unnecessary rebuilds. The flag skips this during bulk processing, and it's done once at the end instead.

**Q: How does the cache handle Redis being unavailable?**

In `cache.py`, on import the code tries `_client.ping()`. If that raises any exception, `REDIS_AVAILABLE` stays `False`. All `cache_get`, `cache_set`, `cache_delete` calls then use a plain Python dict `_mem` with expiry timestamps stored alongside each value. The TTL check happens on read: if `time.time() > expire_at`, the key is deleted and `None` is returned.

**Q: What prevents a user from reviewing the same media twice?**

In `add_review()`:
```python
if db.query(Review).filter_by(user_id=user_id, media_id=media_id).first():
    return "duplicate"
```
One review per (user_id, media_id) pair is enforced at the service layer. During bulk processing, duplicates are logged as `SKIP` events.

**Q: How are recommendations generated?**

Collaborative filtering using cosine similarity on genre taste profiles. Each user has a profile like `{Action: 4.5, Drama: 3.0}`. The cosine similarity between two such vectors measures how aligned their tastes are. The top-3 most similar users are found, then media they rated ≥ 4 (that the target hasn't seen) are recommended, ranked by how many similar users suggested it.

**Q: Why are there two summary tables — `rating_summary` and `review_summaries`?**

`rating_summary` is updated live on every new review via `_update_rating_summary()`. `review_summaries` is updated via `update_review_summary()` from `review_summary_service.py`. The `--rebuild-summaries` command rebuilds both from scratch using aggregation queries. This design separates the incremental live updates from the full rebuild path, making both safer to change independently.

**Q: What pattern does the notification system use?**

The **Observer Pattern**. Users are observers; media items are subjects. Subscriptions are stored in the DB (not memory), so they persist across CLI restarts. When a review is posted, all subscribers of that media get notified. This is a simplified, CLI-based version of what a real event bus or webhook system would do.

---

## 🔧 Redis Setup (Optional)

The app works without Redis. If you want to enable Redis caching:

**Windows (via WSL):**
```bash
sudo apt install redis-server
sudo service redis-server start
redis-cli ping   # should return PONG
```

The Redis connection is configured in `app/cache.py` — update the `host` if your Redis is on a different address.

---

## 📝 Notes for Developers

- All DB sessions are opened and closed explicitly (`db = SessionLocal()` → `db.close()`). There is no context manager / dependency injection framework.
- The project does not use any web framework (no Flask/FastAPI). It is purely a CLI application.
- The `--token` requirement for write commands is a deliberate security design to prevent casual misuse — it mirrors how REST APIs require Authorization headers.
- The `reviews.csv` file included in the project can be used directly with `--bulk-review` for demo purposes.
- `logs/bulk_reviews.log` grows indefinitely. In production, you'd add log rotation.
- SQLite is used for simplicity. In production, replace with PostgreSQL by changing the connection string in `app/db.py`.
