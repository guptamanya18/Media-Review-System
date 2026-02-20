
import argparse, sys


p = argparse.ArgumentParser(
    prog="media_review.py",
    description="Media Review System CLI",
    formatter_class=argparse.RawTextHelpFormatter
)

# Auth
p.add_argument("--register", nargs=2, metavar=("USER", "PASS"),
               help="Register a new account")
p.add_argument("--login",    nargs=2, metavar=("USER", "PASS"),
               help="Login and get your session token")
p.add_argument("--logout",   action="store_true",
               help="Logout and invalidate token")

# Security token (required for all write operations)
p.add_argument("--token", metavar="TOKEN",
               help="Your session token (required for review commands)")

# Browse — no login required
p.add_argument("--list",       action="store_true",    help="List all media")
p.add_argument("--search",     metavar="TITLE",        help="Search media by title")
p.add_argument("--top-rated",  action="store_true",    help="Show top rated media")
p.add_argument("--recommend",  type=int, metavar="USER_ID", help="Get recommendations for a user")
p.add_argument("--insights",   type=int, metavar="MEDIA_ID", help="Analyse reviews for a media")
p.add_argument("--view-reviews", type=int, metavar="MEDIA_ID", help="View all reviews for a media")

# Reviews — require --token
p.add_argument("--review",      nargs=3, metavar=("MEDIA_ID", "RATING", "COMMENT"),
               help="Add a review (requires --token)")
p.add_argument("--bulk-review", metavar="FILE",
               help="Bulk add reviews from CSV (requires --token)")
p.add_argument("--view-bulk-log", action="store_true",
               help="View bulk review log history")

# Concurrent queued reviews — require --token
for i in range(1, 11):
    p.add_argument(f"--review{i}", nargs=3,
                   metavar=("MEDIA_ID", "RATING", "COMMENT"),
                   help=argparse.SUPPRESS)

p.add_argument("--process-queue", action="store_true",
               help="Process all queued reviews (requires --token)")
p.add_argument("--queue-status",  action="store_true",
               help="Show review queue status")

# Notifications — require login
p.add_argument("--notification",    type=int, metavar="MEDIA_ID",
               help="Subscribe to notifications for a media")
p.add_argument("--my-notifications", action="store_true",
               help="Show all notifications for subscribed media")

# Admin — require login
p.add_argument("--add-media", nargs=4, metavar=("TITLE", "TYPE", "GENRE", "YEAR"),
               help="Add a new media entry")
p.add_argument("--rebuild-summaries", action="store_true",
               help="Rebuild all rating/review summaries")

args = p.parse_args()


def _db():
    from app.db import SessionLocal
    return SessionLocal()


def _require_token():
    """
    Reviews and write operations must pass --token explicitly.
    This is the security gate — validates the token against the DB.
    Returns user_id or exits with a clear error.
    """
    if not args.token:
        print("")
        print("  ERROR: Authentication Required")
        print("  " + "-" * 45)
        print("  This command requires --token <your-token>.")
        print("  Your token is displayed after login.")
        print("")
        print("  Step 1: python media_review.py --login <user> <pass>")
        print("  Step 2: Copy the token shown after login.")
        print("  Step 3: Re-run your command with --token <token>")
        print("")
        sys.exit(1)

    from services.auth_service import validate_token_arg
    uid = validate_token_arg(args.token)
    if not uid:
        print("")
        print("  ERROR: Invalid or Expired Token")
        print("  " + "-" * 45)
        print("  The token you provided is not valid or has expired.")
        print("  Tokens expire after 30 minutes.")
        print("")
        print("  Login again to get a fresh token:")
        print("  python media_review.py --logout")
        print("  python media_review.py --login <user> <pass>")
        print("")
        sys.exit(1)
    return uid


def _require_login():
    """For non-review write commands — uses .session file."""
    from services.auth_service import get_current_user_id
    uid = get_current_user_id()
    if not uid:
        print("")
        print("  ERROR: Not Logged In")
        print("  " + "-" * 30)
        print("  Run: python media_review.py --login <user> <pass>")
        print("")
        sys.exit(1)
    return uid


if args.register:
    from services.auth_service import register
    register(args.register[0], args.register[1])
    sys.exit(0)

if args.login:
    from services.auth_service import login
    login(args.login[0], args.login[1])
    sys.exit(0)

if args.logout:
    from services.auth_service import logout
    logout()
    sys.exit(0)



if args.list:
    from services.media_service import list_media
    db = _db()
    list_media(db)
    db.close()
    sys.exit(0)

if args.search:
    from services.media_service import search_media
    search_media(args.search)
    sys.exit(0)

if args.top_rated:
    from services.media_service import get_top_rated
    get_top_rated()
    sys.exit(0)

if args.recommend:
    from services.recommender import recommend_media
    db = _db()
    recommend_media(args.recommend, db)
    db.close()
    sys.exit(0)

if args.view_reviews:
    from services.review_service import view_reviews
    db = _db()
    view_reviews(db, args.view_reviews)
    db.close()
    sys.exit(0)

if args.insights:
    from services.review_analytics import analyze_media
    db = _db()
    stats = analyze_media(args.insights, db)
    db.close()
    if not stats:
        print("")
        print(f"  No reviews found for Media ID {args.insights}.")
        print("")
    else:
        print("")
        print(f"  Review Insights - Media ID {args.insights}")
        print("  " + "=" * 40)
        print(f"  {'Average Rating':<20}: {stats['avg']} / 5")
        print(f"  {'Total Reviews':<20}: {stats['total']}")
        print(f"  {'Positive Sentiment':<20}: {stats['positive']}")
        print(f"  {'Negative Sentiment':<20}: {stats['negative']}")
        print(f"  {'Top Keywords':<20}: {', '.join(stats['top_words'])}")
        print("")
    sys.exit(0)

if args.queue_status:
    from services.async_review_queue import show_queue_status
    show_queue_status()
    sys.exit(0)

if args.view_bulk_log:
    from services.bulk_logger import show_recent_logs
    show_recent_logs()
    sys.exit(0)



if args.review:
    uid = _require_token()
    from services.review_service import add_review
    db = _db()
    add_review(db, uid, int(args.review[0]), int(args.review[1]), args.review[2])
    db.close()
    sys.exit(0)

if args.bulk_review:
    uid = _require_token()
    import asyncio
    from services.review_service import bulk_review_async
    db = _db()
    asyncio.run(bulk_review_async(args.bulk_review, db, uid))
    db.close()
    sys.exit(0)

# Queued reviews --review1 to --review10 — require --token
queued = None
for i in range(1, 11):
    v = getattr(args, f"review{i}", None)
    if v:
        queued = v
        break

if queued:
    uid = _require_token()
    from services.async_review_queue import enqueue_review
    enqueue_review(uid, int(queued[0]), int(queued[1]), queued[2])
    sys.exit(0)

if args.process_queue:
    _require_token()
    from services.async_review_queue import process_queue
    process_queue()
    sys.exit(0)



if args.notification:
    uid = _require_login()
    from services.notification_service import subscribe, show_notifications
    db = _db()
    subscribe(db, uid, args.notification)
    show_notifications(uid, args.notification)
    db.close()
    sys.exit(0)

if args.my_notifications:
    uid = _require_login()
    from services.notification_service import show_notifications
    show_notifications(uid)
    sys.exit(0)

if args.add_media:
    _require_login()
    from services.media_service import add_media
    db = _db()
    title, mtype, genre, year = args.add_media
    add_media(db, title, genre, int(year), mtype)
    db.close()
    sys.exit(0)

if args.rebuild_summaries:
    _require_login()
    from services.rebuild_summary import rebuild_all
    rebuild_all()
    sys.exit(0)

p.print_help()
