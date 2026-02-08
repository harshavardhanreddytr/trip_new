import os
import time
import uuid
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
import json
import math
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from db import init_db, get_db
from functools import wraps
load_dotenv()
app = Flask(__name__)
app.secret_key = "tripplanner-dev-secret"

# Optimize Flask configuration for better performance
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files

# Request timing middleware
@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request_time(response):
    if hasattr(g, 'start_time'):
        total_time = (time.time() - g.start_time) * 1000
        if total_time > 500:  # Log slow requests
            print(f">>> SLOW REQUEST: {request.method} {request.path} - {total_time:.1f}ms")
        elif total_time > 100:
            print(f">>> Request: {request.method} {request.path} - {total_time:.1f}ms")
    return response

@app.teardown_request
def close_db(error=None):
    db = g.pop("db_conn", None)
    if db is not None:
        db.close()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)  # Session lasts 31 days
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# init_db() will be called in application context when the server starts

def uid():
    return str(uuid.uuid4())

# temporary in-memory storage

def task_completion_stats(conn, where_clause="", params=()):
    cur = conn.cursor()
    
    cur.execute(
        f"""
        SELECT COUNT(*) 
        FROM tasks
        WHERE is_deleted = false
        {where_clause}
        """,
        params
    )
    total = cur.fetchone()[0]

    cur.execute(
        f"""
        SELECT COUNT(DISTINCT task_id)
        FROM task_status_events
        WHERE status = %s
        AND task_id IN (
            SELECT id FROM tasks
            WHERE is_deleted = false
            {where_clause}
        )
        """,
        ('YES',) + params
    )
    completed = cur.fetchone()[0]

    cur.execute(
        f"""
        SELECT COUNT(DISTINCT task_id)
        FROM task_status_events
        WHERE status = %s
        AND task_id IN (
            SELECT id FROM tasks
            WHERE is_deleted = false
            {where_clause}
        )
        """,
        ('SKIPPED',) + params
    )
    skipped = cur.fetchone()[0]
    
    cur.close()

    unanswered = max(total - completed - skipped, 0)

    result = {
        "total": total,
        "completed": completed,
        "skipped": skipped,
        "unanswered": unanswered
    }
    
    return result



def average_delay_minutes(conn, task_filter_sql="", params=()):
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT eta_minutes
            FROM eta_snapshots
            WHERE task_id IN (
                SELECT id FROM tasks
                WHERE is_deleted = false
                {task_filter_sql}
            )
            """,
            params
        )
        rows = cur.fetchall()
        cur.close()
        
        if not rows:
            return 0
        
        total_minutes = sum(row[0] for row in rows if row[0] is not None)
        return total_minutes // len(rows) if len(rows) > 0 else 0
        
    except Exception as e:
        print(f"DEBUG: eta_snapshots table error: {e}")
        return 0  # Return 0 delay if table doesn't exist or query fails

def delay_time_buckets(conn, trip_id):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.start_time
            FROM tasks t
            JOIN eta_snapshots e ON e.task_id = t.id
            WHERE t.trip_id = %s
            AND t.is_deleted = false
        """, (trip_id,))
        rows = cur.fetchall()
        cur.close()
        
        buckets = {"morning": 0, "afternoon": 0, "evening": 0}
        
        for row in rows:
            hour = int(row["start_time"].split(":")[0])
            if 6 <= hour < 12:
                buckets["morning"] += 1
            elif 12 <= hour < 18:
                buckets["afternoon"] += 1
            else:
                buckets["evening"] += 1
        
        return buckets
        
    except Exception as e:
        print(f"DEBUG: delay_time_buckets error: {e}")
        return {"morning": 0, "afternoon": 0, "evening": 0}

def overall_analytics(user_id):
    conn = get_db()

    # Get trip IDs where user is owner OR member
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT t.id 
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.owner_id = %s OR tm.user_id = %s
    """, (user_id, user_id))
    trip_ids = [r["id"] for r in cur.fetchall()]
    cur.close()

    if not trip_ids:
        return {"tasks": {"total": 0, "completed": 0, "skipped": 0, "unanswered": 0}}

    placeholders = ",".join("?" * len(trip_ids))

    stats = task_completion_stats(
        conn,
        f"AND trip_id IN ({placeholders})",
        trip_ids
    )
    
    avg_delay = average_delay_minutes(
        conn,
        f"AND trip_id IN ({placeholders})",
        trip_ids
    )

    result = {
        "trip_count": len(trip_ids),
        "tasks": stats,
        "average_delay_minutes": avg_delay
    }
    
    return result

def trip_analytics(trip_id):
    conn = get_db()

    stats = task_completion_stats(
        conn,
        "AND trip_id = %s",
        (trip_id,)
    )

    avg_delay = average_delay_minutes(
        conn,
        "AND trip_id = %s",
        (trip_id,)
    )

    buckets = delay_time_buckets(conn, trip_id)

    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM days WHERE trip_id = %s",
        (trip_id,)
    )
    days_count = cur.fetchone()[0]
    cur.close()

    return {
        "days": days_count,
        "tasks": stats,
        "average_delay_minutes": avg_delay,
        "delay_windows": buckets
    }
def day_analytics(day_id):
    conn = get_db()

    stats = task_completion_stats(
        conn,
        "AND day_id = %s",
        (day_id,)
    )

    avg_delay = average_delay_minutes(
        conn,
        "AND day_id = %s",
        (day_id,)
    )

    return {
        "tasks": stats,
        "average_delay_minutes": avg_delay
    }

def table_exists(conn, table_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' AND table_name=%s
    """, (table_name,))
    result = cur.fetchone() is not None
    cur.close()
    return result

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Ensure g is properly available and current_user is set
        if not hasattr(g, 'current_user') or not g.current_user:
            flash("Please login first")
            return redirect(url_for("auth"))
        return fn(*args, **kwargs)
    return wrapper

def make_public_id(user_id):
    return "TP-" + user_id.split("-")[0][:6].upper()

def resolve_public_id(public_id, conn):
    """Convert public ID like 'TP-ABC123' back to full user ID"""
    if not public_id.startswith("TP-"):
        return None
    
    prefix = public_id[3:].lower()  # Remove "TP-" and convert to lowercase
    
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM users 
        WHERE LOWER(SUBSTR(id, 1, 6)) = %s
    """, (prefix,))
    user = cur.fetchone()
    cur.close()
    
    return user["id"] if user else None



@app.route("/_ping")
def _ping():
    return "pong"

@app.route("/ping")
def ping():
    """Fast endpoint for testing latency without DB calls"""
    return {"status": "ok", "timestamp": time.time()}

@app.route("/ping-db")  
def ping_db():
    """Test endpoint with DB connection for measuring DB latency"""
    start = time.time()
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT 1")
    result = cur.fetchone()
    cur.close()
    db_time = (time.time() - start) * 1000
    return {"status": "ok", "db_time_ms": f"{db_time:.1f}", "result": result[0]}

@app.route("/")
def auth():
    return render_template("auth.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm")

    if password != confirm:
        flash("Passwords do not match")
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT 1 FROM users WHERE name = %s",
        (username,)
    )
    exists = cur.fetchone()

    if exists:
        cur.close()
        flash("User already exists")
        return redirect(url_for("auth"))

    user_id = str(uuid.uuid4())
    now = datetime.now().isoformat()

    cur.execute("""
        INSERT INTO users (id, name, password, created_at)
        VALUES (%s, %s, %s, %s)
    """, (user_id, username, password, now))

    conn.commit()
    cur.close()

    flash("Successfully registered! Please login.")
    return redirect(url_for("auth"))


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE name = %s",
        (username,)
    )
    user = cur.fetchone()
    cur.close()

    if not user:
        flash("User not found")
        return redirect(url_for("auth"))

    # TEMP plain-text check
    if password != user["password"]:
        flash("Invalid credentials")
        return redirect(url_for("auth"))

    # ✅ SET SESSION HERE
    session.clear()
    session["user_id"] = user["id"]
    session.permanent = True  # Make session persistent
    
    print("LOGIN OK → session user_id:", session["user_id"])

    return redirect(url_for("dashboard"))

@app.route("/forgot", methods=["POST"])
def forgot():
    username = request.form.get("username")  # assuming username=name

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM users WHERE name = %s",
        (username,)
    )
    user = cur.fetchone()
    cur.close()

    if user:
        flash("Password reset link would be sent (mock).")
    else:
        flash("User not found")

    return redirect(url_for("auth"))


@app.before_request
def load_current_user():
    user_id = session.get("user_id")
    
    # Reset current_user for new request
    g.current_user = None

    if user_id:
        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
            user = cur.fetchone()

            cur.close()

            g.current_user = user
            
        except Exception as e:
            print(f">>> ❌ Error loading user in before_request: {e}")
            # Don't fail the entire request, just log the error
            g.current_user = None

    print("REQUEST:", request.path,
          "| session:", session.get("user_id"),
          "| g.current_user:", bool(g.current_user))

@app.route("/profile")
@login_required
def profile():
    user = g.current_user

    # MVP fallback (TEMP)
    if not user:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users ORDER BY created_at LIMIT 1"
        )
        user = cur.fetchone()
        cur.close()

    if not user:
        return redirect(url_for("auth"))

    public_id = make_public_id(user["id"])
    
    # Calculate real stats
    conn = get_db()
    cur = conn.cursor()
    
    # Get trips count (owned + member)
    cur.execute("""
        SELECT COUNT(DISTINCT t.id) as count 
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.owner_id = %s OR tm.user_id = %s
    """, (user["id"], user["id"]))
    trips_count = cur.fetchone()["count"]
    
    # Get task completion rate
    cur.execute("""
        SELECT COUNT(*) as count FROM tasks t
        JOIN days d ON t.day_id = d.id
        JOIN trips tr ON d.trip_id = tr.id
        LEFT JOIN trip_members tm ON tr.id = tm.trip_id
        WHERE (tr.owner_id = %s OR tm.user_id = %s) AND t.is_deleted = false
    """, (user["id"], user["id"]))
    total_tasks = cur.fetchone()["count"]
    
    cur.execute("""
        SELECT COUNT(DISTINCT t.id) as count FROM tasks t
        JOIN days d ON t.day_id = d.id
        JOIN trips tr ON d.trip_id = tr.id
        LEFT JOIN trip_members tm ON tr.id = tm.trip_id
        JOIN task_status_events tse ON t.id = tse.task_id
        WHERE (tr.owner_id = %s OR tm.user_id = %s) AND t.is_deleted = false AND tse.status = %s
    """, (user["id"], user["id"], 'YES'))
    completed_tasks = cur.fetchone()["count"]
    
    task_completion_rate = f"{int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)}%"
    
    # Get friend count
    cur.execute(
        "SELECT COUNT(*) as count FROM friends WHERE user_id = %s",
        (user["id"],)
    )
    friends_count = cur.fetchone()["count"]
    
    cur.close()
    
    stats = {
        "trips_completed": trips_count,
        "task_completion_rate": task_completion_rate,
        "average_delay": "~5 min",  # Placeholder for now
        "most_used_transport": "Walk",  # Placeholder for now
        "friends_count": friends_count
    }

    return render_template(
        "profile.html",
        user=user,
        public_id=public_id,
        stats=stats
    )

def csv_to_trip_json(csv_file):
    """
    Convert CSV file to the internal JSON structure.
    CSV columns: trip_name, trip_start, trip_end, day_date, time, title, lat, lng, description
    """
    csv_file.stream.seek(0)
    content = csv_file.read().decode('utf-8-sig')  # Handle BOM if present
    lines = content.splitlines()
    
    if not lines:
        raise ValueError("CSV file is empty")
    
    # Use csv.reader with proper quoting to handle commas in values
    try:
        reader = csv.DictReader(lines, quoting=csv.QUOTE_ALL)
        rows = []
        for row_num, row in enumerate(reader, 2):  # Start at 2 since row 1 is header
            # Skip completely empty rows
            if not any(value.strip() for value in row.values() if value):
                continue
            rows.append((row_num, row))
    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {str(e)}. Ensure commas in text are properly quoted.")
    
    if not rows:
        raise ValueError("No data rows found in CSV")
    
    # Validate required columns
    required_cols = ['trip_name', 'trip_start', 'trip_end', 'day_date', 'time', 'title']
    if reader.fieldnames is None:
        raise ValueError("No column headers found")
        
    missing_cols = [col for col in required_cols if col not in reader.fieldnames]
    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Extract trip info from first row
    first_row_num, first_row = rows[0]
    trip_name = first_row.get('trip_name', '').strip()
    trip_start = first_row.get('trip_start', '').strip()
    trip_end = first_row.get('trip_end', '').strip()
    
    if not trip_name or not trip_start or not trip_end:
        raise ValueError("trip_name, trip_start, and trip_end must not be empty")
    
    # Validate date formats
    try:
        datetime.strptime(trip_start, '%Y-%m-%d')
        datetime.strptime(trip_end, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Date format error - {str(e)}. Use YYYY-MM-DD format")
    
    # Group tasks by day_date
    days_dict = {}
    for row_num, row in rows:
        day_date = row.get('day_date', '').strip()
        if not day_date:
            continue
        
        # Validate day_date format
        try:
            datetime.strptime(day_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Row {row_num}: Invalid day_date format: '{day_date}'. Must be YYYY-MM-DD")
        
        title = row.get('title', '').strip()
        time_str = row.get('time', '').strip()
        description = row.get('description', '').strip()
        lat = row.get('lat', '').strip()
        lng = row.get('lng', '').strip()
        
        if not title:
            raise ValueError(f"Row {row_num}: Task title cannot be empty")
        if not time_str:
            raise ValueError(f"Row {row_num}: Task time cannot be empty")
        
        # Validate time format (HH:MM)
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            raise ValueError(f"Row {row_num}: Invalid time format: '{time_str}'. Must be HH:MM (24-hour format)")
        
        task = {
            "title": title,
            "start_time": time_str,
            "end_time": time_str,  # Same as start_time
            "description": description
        }
        
        # Add optional lat/lng - be more lenient with validation
        if lat and lat.replace('.', '').replace('-', '').replace('+', '').isdigit():
            try:
                task["lat"] = float(lat)
            except ValueError:
                pass  # Ignore invalid lat instead of failing
        
        if lng and lng.replace('.', '').replace('-', '').replace('+', '').isdigit():
            try:
                task["lng"] = float(lng)
            except ValueError:
                pass  # Ignore invalid lng instead of failing
        
        if day_date not in days_dict:
            days_dict[day_date] = []
        days_dict[day_date].append((time_str, task))
    
    if not days_dict:
        raise ValueError("No valid tasks found in CSV")
    
    # Sort tasks within each day by time
    days = []
    for day_date in sorted(days_dict.keys()):
        tasks_with_time = days_dict[day_date]
        tasks_with_time.sort(key=lambda x: x[0])  # Sort by time
        tasks = [task for _, task in tasks_with_time]
        
        days.append({
            "date": day_date,
            "tasks": tasks
        })
    
    return {
        "trip_name": trip_name,
        "start_date": trip_start,
        "end_date": trip_end,
        "days": days
    }


@app.route("/import-trip", methods=["POST"])
def import_trip():
    print(">>> IMPORT ROUTE HIT", flush=True)
    file = request.files.get("trip_file")

    if not file or not file.filename:
        flash("No file uploaded")
        return redirect(url_for("import_trips_page"))
    
    print(f">>> Processing file: {file.filename}", flush=True)
    
    # Handle CSV files
    if file.filename.endswith(".csv"):
        try:
            print(">>> Parsing CSV...", flush=True)
            data = csv_to_trip_json(file)
            print(f">>> CSV parsed successfully: {data.get('trip_name')}", flush=True)
        except ValueError as e:
            print(f">>> CSV Error: {str(e)}", flush=True)
            flash(f"CSV Error: {str(e)}")
            return redirect(url_for("import_trips_page"))
        except Exception as e:
            print(f">>> Unexpected CSV error: {str(e)}", flush=True)
            flash(f"Failed to parse CSV: {str(e)}")
            return redirect(url_for("import_trips_page"))
    elif file.filename.endswith(".json"):
        try:
            print(">>> Parsing JSON...", flush=True)
            data = json.load(file)
            print(f">>> JSON parsed successfully", flush=True)
        except Exception as e:
            print(f">>> JSON Error: {str(e)}", flush=True)
            flash(f"Failed to parse JSON: {str(e)}")
            return redirect(url_for("import_trips_page"))
    else:
        print(f">>> Invalid file format: {file.filename}", flush=True)
        flash("Invalid file format. Please upload a CSV or JSON file.")
        return redirect(url_for("import_trips_page"))

    # At this point, 'data' is in the canonical JSON structure (from CSV or JSON)
    try:
        print(">>> Starting database operations...", flush=True)
        trip_id = uid()
        trip_name = data.get("trip_name")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        
        print(f">>> Trip details: {trip_name}, {start_date} to {end_date}", flush=True)
        
        # Check current user
        if not hasattr(g, 'current_user') or not g.current_user:
            print(">>> No current user found, using fallback", flush=True)
            owner_id = "user_1"  # Fallback user
        else:
            owner_id = g.current_user["id"]
            print(f">>> Using current user: {owner_id}", flush=True)

        conn = get_db()
        cur = conn.cursor()
        now = datetime.now().isoformat()

        # Insert trip
        print(">>> Inserting trip...", flush=True)
        cur.execute("""
            INSERT INTO trips (id, name, start_date, end_date, owner_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (trip_id, trip_name, start_date, end_date, owner_id, now))

        # Insert owner as member
        print(">>> Adding trip member...", flush=True)
        cur.execute("""
            INSERT INTO trip_members (trip_id, user_id, role, joined_at)
            VALUES (%s, %s, %s, %s)
        """, (trip_id, owner_id, "owner", now))

        # Insert days & tasks
        print(f">>> Processing {len(data.get('days', []))} days...", flush=True)
        for day_idx, day in enumerate(data.get("days", [])):
            day_id = uid()
            day_date = day["date"]
            
            print(f">>> Processing day {day_idx + 1}: {day_date} with {len(day.get('tasks', []))} tasks", flush=True)

            cur.execute("""
                INSERT INTO days (id, trip_id, date)
                VALUES (%s, %s, %s)
            """, (day_id, trip_id, day_date))

            for idx, task in enumerate(day.get("tasks", [])):
                task_id = uid()

                cur.execute("""
                    INSERT INTO tasks (
                        id, trip_id, day_id,
                        title, description,
                        start_time, end_time,
                        lat, lng,
                        order_index, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    task_id,
                    trip_id,
                    day_id,
                    task.get("title"),
                    task.get("description", ""),
                    task.get("start_time"),
                    task.get("end_time"),
                    task.get("lat"),
                    task.get("lng"),
                    idx,
                    now
                ))

        #conn.commit()
        cur.close()
        
        print(">>> Trip imported successfully!", flush=True)
        flash("Trip imported successfully")
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        print(f">>> Database error: {str(e)}", flush=True)
        flash(f"Database error: {str(e)}")
        return redirect(url_for("import_trips_page"))


@app.route("/trip/<trip_id>/delete", methods=["POST"])
@login_required
def delete_trip(trip_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Check if trip exists and user is owner
    cur.execute(
        "SELECT * FROM trips WHERE id = %s AND owner_id = %s",
        (trip_id, g.current_user["id"])
    )
    trip = cur.fetchone()
    
    if not trip:
        cur.close()
        flash("Trip not found or you don't have permission to delete it")
        return redirect(url_for("trips_page"))
    
    try:
        # Delete in order to respect foreign key constraints
        # 1. Delete location updates
        cur.execute("""
            DELETE FROM location_updates 
            WHERE transport_group_id IN (
                SELECT id FROM transport_groups WHERE trip_id = %s
            )
        """, (trip_id,))
        
        # 2. Delete transport group members
        cur.execute("""
            DELETE FROM transport_group_members 
            WHERE transport_group_id IN (
                SELECT id FROM transport_groups WHERE trip_id = %s
            )
        """, (trip_id,))
        
        # 3. Delete transport groups
        cur.execute("DELETE FROM transport_groups WHERE trip_id = %s", (trip_id,))
        
        # 4. Delete task status events
        cur.execute("""
            DELETE FROM task_status_events 
            WHERE task_id IN (
                SELECT id FROM tasks WHERE trip_id = %s
            )
        """, (trip_id,))
        
        # 5. Delete task assignments
        cur.execute("""
            DELETE FROM task_assignments 
            WHERE task_id IN (
                SELECT id FROM tasks WHERE trip_id = %s
            )
        """, (trip_id,))
        
        # 6. Delete tasks
        cur.execute("DELETE FROM tasks WHERE trip_id = %s", (trip_id,))
        
        # 7. Delete days
        cur.execute("DELETE FROM days WHERE trip_id = %s", (trip_id,))
        
        # 8. Delete trip members
        cur.execute("DELETE FROM trip_members WHERE trip_id = %s", (trip_id,))
        
        # 9. Finally delete the trip
        cur.execute("DELETE FROM trips WHERE id = %s", (trip_id,))
        
        conn.commit()
        cur.close()
        
        conn.commit()
        
        flash(f"Trip '{trip['name']}' has been deleted successfully")
        return redirect(url_for("trips_page"))
        
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting trip: {str(e)}")
        return redirect(url_for("trips_page"))
        print(f">>> Database error: {str(e)}", flush=True)
        flash(f"Database error: {str(e)}")
        return redirect(url_for("import_trips_page"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trips WHERE owner_id = %s ORDER BY created_at DESC", 
                        (g.current_user["id"],))
    trips = cur.fetchall()
    cur.close()
    return render_template("dashboard.html", trips=trips)

@app.route("/analytics")
@login_required
def analytics():
    scope = request.args.get("scope", "overall")
    trip_id = request.args.get("trip_id")
    day_id = request.args.get("day_id")

    user_id = g.current_user["id"]

    if scope == "overall":
        data = overall_analytics(user_id)

    elif scope == "trip" and trip_id:
        data = trip_analytics(trip_id)

    elif scope == "day" and day_id:
        data = day_analytics(day_id)

    else:
        return {"error": "Invalid analytics scope"}, 400

    return data

@app.route("/analytics-ui")
@login_required
def analytics_ui():
    conn = get_db()
    cur = conn.cursor()
    # Get trips where user is owner OR member
    cur.execute("""
        SELECT DISTINCT t.id, t.name
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.owner_id = %s OR tm.user_id = %s
        ORDER BY t.name ASC
    """, (g.current_user["id"], g.current_user["id"]))
    trips = cur.fetchall()
    cur.close()
    return render_template("analytics.html", trips=trips)

@app.route("/trips")
@login_required
def trips_page():
    conn = get_db()
    cur = conn.cursor()
    # Get trips where user is owner OR member
    cur.execute("""
        SELECT DISTINCT t.*, tm.role
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.owner_id = %s OR tm.user_id = %s
        ORDER BY t.created_at DESC
    """, (g.current_user["id"], g.current_user["id"]))
    trips = cur.fetchall()
    cur.close()
    return render_template("trips.html", trips=trips)

@app.route("/import-trips")
@login_required
def import_trips_page():
    return render_template("import_trips.html")

@app.route("/friends")
@login_required
def friends_page():
    try:
        user_id = g.current_user["id"]
        conn = get_db()
        cur = conn.cursor()

        # Get friends list
        cur.execute("""
            SELECT u.id, u.name
            FROM friends f
            JOIN users u ON u.id = f.friend_id
            WHERE f.user_id = %s
        """, (user_id,))
        friends = cur.fetchall()
        
        # Get pending friend requests
        cur.execute("""
            SELECT fr.id, fr.sender_id, u.name as sender_name, fr.message, fr.created_at
            FROM friend_requests fr
            JOIN users u ON u.id = fr.sender_id
            WHERE fr.receiver_id = %s AND fr.status = %s
        """, (user_id, 'pending'))
        pending = cur.fetchall()

        cur.close()

        return render_template(
            "friends.html",
            friends=friends,
            pending=pending,
            current_user=g.current_user,
            public_id=make_public_id(g.current_user["id"])
        )
    except Exception as e:
        print(f"Error in friends_page: {e}")
        flash("Error loading friends page. Please try again.", "error")
        return redirect("/dashboard")


@app.route("/friends/add", methods=["POST"])
@login_required
def add_friend():
    try:
        sender_id = g.current_user["id"]
        friend_public_id = request.form.get("friend_id", "").strip()
        message = request.form.get("message", "")

        if not friend_public_id:
            flash("Member ID required", "error")
            return redirect("/friends")

        conn = get_db()
        
        # Resolve public ID to actual user ID
        receiver_id = resolve_public_id(friend_public_id, conn)
        
        if not receiver_id:
            flash("User not found. Please check the Member ID and try again.", "error")
            return redirect("/friends")

        if sender_id == receiver_id:
            flash("You cannot add yourself as a friend", "error")
            return redirect("/friends")

        cur = conn.cursor()
        
        # Check if already friends
        cur.execute("""
            SELECT 1 FROM friends
            WHERE user_id = %s AND friend_id = %s
        """, (sender_id, receiver_id))
        already_friends = cur.fetchone()

        if already_friends:
            cur.close()
            flash("You are already friends with this person!", "info")
            return redirect("/friends")

        # Check if request already exists
        cur.execute("""
            SELECT 1 FROM friend_requests
            WHERE sender_id = %s AND receiver_id = %s AND status = %s
        """, (sender_id, receiver_id, 'pending'))
        request_exists = cur.fetchone()

        if request_exists:
            cur.close()
            flash("Friend request already sent to this person!", "info")
            return redirect("/friends")

        # Create friend request
        request_id = uid()
        now = datetime.now().isoformat()

        cur.execute("""
            INSERT INTO friend_requests (id, sender_id, receiver_id, message, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (request_id, sender_id, receiver_id, message, 'pending', now))

        conn.commit()
        cur.close()

        flash(f"Friend request sent successfully! 🎉", "success")
        return redirect("/friends")
        
    except Exception as e:
        print(f"Error in add_friend: {e}")
        flash("Error sending friend request. Please try again.", "error")
        return redirect("/friends")




@app.route("/friends/accept/<sender_id>")
@login_required
def accept_friend(sender_id):
    user_id = g.current_user["id"]
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now().isoformat()

    try:
        # Check if friend request exists
        cur.execute("""
            SELECT id FROM friend_requests
            WHERE sender_id = %s AND receiver_id = %s AND status = %s
        """, (sender_id, user_id, 'pending'))
        request_exists = cur.fetchone()
        
        if not request_exists:
            flash("Friend request not found or already processed", "error")
            cur.close()
            return redirect("/friends")
        
        # Check if they're already friends (prevent duplicates)
        cur.execute("""
            SELECT 1 FROM friends
            WHERE user_id = %s AND friend_id = %s
        """, (user_id, sender_id))
        already_friends = cur.fetchone()
        
        if not already_friends:
            # Add both directions to friends table
            cur.execute("""
                INSERT INTO friends (user_id, friend_id, created_at)
                VALUES (%s, %s, %s)
            """, (user_id, sender_id, now))

            cur.execute("""
                INSERT INTO friends (user_id, friend_id, created_at)
                VALUES (%s, %s, %s)
            """, (sender_id, user_id, now))

        # Update friend request status
        cur.execute("""
            UPDATE friend_requests
            SET status = %s, responded_at = %s
            WHERE sender_id = %s AND receiver_id = %s
        """, ('accepted', now, sender_id, user_id))

        conn.commit()
        cur.close()

        flash("Friend request accepted! 🎉", "success")
        return redirect("/friends")
        
    except Exception as e:
        conn.rollback()
        print(f"Error accepting friend request: {e}")
        flash("Error processing friend request. Please try again.", "error")
        return redirect("/friends")


@app.route("/friends/reject/<sender_id>")
@login_required
def reject_friend(sender_id):
    user_id = g.current_user["id"]
    conn = get_db()
    now = datetime.now().isoformat()

    try:
        # Check if friend request exists
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM friend_requests
            WHERE sender_id = %s AND receiver_id = %s AND status = 'pending'
        """, (sender_id, user_id))
        request_exists = cur.fetchone()
        cur.close()
        
        if not request_exists:
            flash("Friend request not found or already processed", "error")
            return redirect("/friends")

        # Update friend request status to rejected
        cur = conn.cursor()
        cur.execute("""
            UPDATE friend_requests
            SET status = 'rejected', responded_at = %s
            WHERE sender_id = %s AND receiver_id = %s
        """, (now, sender_id, user_id))
        cur.close()

        conn.commit()

        flash("Friend request declined", "info")
        return redirect("/friends")
        
    except Exception as e:
        conn.rollback()
        print(f"Error rejecting friend request: {e}")
        flash("Error processing friend request. Please try again.", "error")
        return redirect("/friends")


@app.route("/trip/<trip_id>/invite-friend", methods=["POST"])
@login_required
def invite_friend_to_trip(trip_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Verify trip ownership
    cur.execute("""
        SELECT * FROM trips WHERE id = %s AND owner_id = %s
    """, (trip_id, g.current_user["id"]))
    trip = cur.fetchone()
    
    if not trip:
        cur.close()
        flash("Trip not found or you don't have permission", "error")
        return redirect("/trips")
    
    friend_public_id = request.form.get("friend_id", "").strip()
    
    if not friend_public_id:
        flash("Please select a friend to invite", "error")
        return redirect(f"/trip/{trip_id}")
    
    # Resolve public ID to user ID
    friend_id = resolve_public_id(friend_public_id, conn)
    
    if not friend_id:
        flash("Friend not found", "error")
        return redirect(f"/trip/{trip_id}")
    
    # Check if already a member
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM trip_members 
        WHERE trip_id = %s AND user_id = %s
    """, (trip_id, friend_id))
    existing_member = cur.fetchone()
    cur.close()
    
    if existing_member:
        flash("This friend is already a member of this trip", "info")
        return redirect(f"/trip/{trip_id}")
    
    # Add friend as trip member
    now = datetime.now().isoformat()
    
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO trip_members (trip_id, user_id, role, joined_at)
            VALUES (%s, %s, 'member', %s)
        """, (trip_id, friend_id, now))
        cur.close()
        conn.commit()
        
        conn.commit()
        
        # Get friend name for message
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE id = %s", (friend_id,))
        friend = cur.fetchone()
        cur.close()
        friend_name = friend["name"] if friend else "Friend"
        
        flash(f"{friend_name} has been added to the trip! 🎉", "success")
        return redirect(f"/trip/{trip_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error inviting friend to trip: {e}")
        flash("Error adding friend to trip. Please try again.", "error")
        return redirect(f"/trip/{trip_id}")


@app.route("/trip/<trip_id>/remove-member/<user_id>", methods=["POST"])
@login_required
def remove_trip_member(trip_id, user_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Verify trip ownership
    cur.execute("""
        SELECT * FROM trips WHERE id = %s AND owner_id = %s
    """, (trip_id, g.current_user["id"]))
    trip = cur.fetchone()
    
    if not trip:
        cur.close()
        flash("Trip not found or you don't have permission", "error")
        return redirect("/trips")
    
    # Don't allow removing the owner
    if user_id == g.current_user["id"]:
        flash("Cannot remove yourself as the trip owner", "error")
        return redirect(f"/trip/{trip_id}")
    
    try:
        # Remove member
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM trip_members 
            WHERE trip_id = %s AND user_id = %s
        """, (trip_id, user_id))
        cur.close()
        conn.commit()
        
        conn.commit()
        
        flash("Member removed from trip", "info")
        return redirect(f"/trip/{trip_id}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error removing trip member: {e}")
        flash("Error removing member. Please try again.", "error")
        return redirect(f"/trip/{trip_id}")


@app.route("/task/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )
    task = cur.fetchone()

    if not task:
        cur.close()
        return "Task not found", 404

    cur.execute(
        "SELECT * FROM days WHERE id = %s",
        (task["day_id"],)
    )
    day = cur.fetchone()

    cur.execute(
        "SELECT * FROM trips WHERE id = %s",
        (task["trip_id"],)
    )
    trip = cur.fetchone()
    cur.close()

    if request.method == "POST":
        title = request.form["title"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET title = %s, start_time = %s, end_time = %s, lat = %s, lng = %s
            WHERE id = %s
        """, (title, start_time, end_time, lat, lng, task_id))
        cur.close()
        conn.commit()

        conn.commit()

        return redirect(
            url_for("day_view", trip_id=trip["id"], day_id=day["id"])
        )

    return render_template(
        "edit_task.html",
        task=task,
        trip=trip,
        day=day
    )

@app.route("/task/<task_id>/add", methods=["GET", "POST"])
def add_task(task_id):
    pos = request.args.get("pos", "after")

    conn = get_db()

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )
    ref_task = cur.fetchone()
    cur.close()

    if not ref_task:
        return "Reference task not found", 404

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM days WHERE id = %s",
        (ref_task["day_id"],)
    )
    day = cur.fetchone()
    cur.close()

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM trips WHERE id = %s",
        (ref_task["trip_id"],)
    )
    trip = cur.fetchone()
    cur.close()

    if request.method == "POST":
        title = request.form["title"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]
        lat = request.form.get("lat")
        lng = request.form.get("lng")

        base_index = ref_task["order_index"]

        if pos == "before":
            new_index = base_index - 0.5
        else:
            new_index = base_index + 0.5

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tasks (
                id, trip_id, day_id,
                title, description,
                start_time, end_time,
                lat, lng,
                order_index, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            uid(),
            trip["id"],
            day["id"],
            title,
            "",
            start_time,
            end_time,
            lat,
            lng,
            new_index,
            datetime.now().isoformat()
        ))
        cur.close()
        conn.commit()

        conn.commit()

        return redirect(
            url_for("day_view", trip_id=trip["id"], day_id=day["id"])
        )

    return render_template(
        "add_task.html",
        trip=trip,
        day=day,
        ref_task=ref_task,
        position=pos
    )

@app.route("/task/<task_id>/delete", methods=["POST", "GET"])
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )
    task = cur.fetchone()

    if not task:
        cur.close()
        if request.method == "POST" or request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "message": "Task not found"}), 404
        return "Task not found", 404

    cur.execute(
        "UPDATE tasks SET is_deleted = true WHERE id = %s",
        (task_id,)
    )
    conn.commit()
    cur.close()

    if request.method == "POST" or request.headers.get('Accept') == 'application/json':
        return jsonify({"success": True, "message": "Task deleted successfully"})
    else:
        # For GET requests, redirect back to day view
        return redirect(
            url_for("day_view",
                    trip_id=task["trip_id"],
                    day_id=task["day_id"])
        )

@app.route("/task/<task_id>/status/<status>", methods=["POST"])
def update_task_status(task_id, status):
    if status not in ("YES", "NO", "SKIPPED"):
        return {"success": False, "error": "Invalid status"}, 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )
    task = cur.fetchone()

    if not task:
        cur.close()
        return {"success": False, "error": "Task not found"}, 404

    # Insert status event instead of updating task directly
    cur.execute("""
        INSERT INTO task_status_events (id, task_id, user_id, status, responded_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        uid(),
        task_id,
        g.current_user["id"],
        status,
        datetime.now().isoformat()
    ))
    cur.close()
    conn.commit()

    conn.commit()

    return {"success": True, "status": status}


@app.route("/task/<task_id>/status/reset", methods=["POST"])
def reset_task_status(task_id):
    conn = get_db()

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )
    task = cur.fetchone()
    cur.close()

    if not task:
        return {"success": False, "error": "Task not found"}, 404

    # Delete all status events for this task
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM task_status_events WHERE task_id = %s",
        (task_id,)
    )
    cur.close()
    conn.commit()

    conn.commit()

    return {"success": True}


@app.route("/trip/<trip_id>")
@login_required
def trip_view(trip_id):
    conn = get_db()
    cur = conn.cursor()

    # Check if user is owner or member of the trip
    cur.execute("""
        SELECT DISTINCT t.*
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.id = %s AND (t.owner_id = %s OR tm.user_id = %s)
    """, (trip_id, g.current_user["id"], g.current_user["id"]))
    trip = cur.fetchone()

    if not trip:
        cur.close()
        return "Trip not found", 404

    cur.execute("""
        SELECT * FROM days
        WHERE trip_id = %s
        ORDER BY date ASC
    """, (trip_id,))
    days = cur.fetchall()

    # Get trip members
    cur.execute("""
        SELECT tm.user_id, tm.role, tm.joined_at, u.name
        FROM trip_members tm
        JOIN users u ON tm.user_id = u.id
        WHERE tm.trip_id = %s
        ORDER BY tm.role DESC, tm.joined_at ASC
    """, (trip_id,))
    members = cur.fetchall()

    # Get user's friends (for invitation dropdown) with public IDs
    cur.execute("""
        SELECT u.id, u.name
        FROM friends f
        JOIN users u ON u.id = f.friend_id
        WHERE f.user_id = %s
    """, (g.current_user["id"],))
    friends = cur.fetchall()
    cur.close()
    
    # Convert to list with public IDs
    friends_with_public_ids = []
    for friend in friends:
        friends_with_public_ids.append({
            'id': friend['id'],
            'public_id': make_public_id(friend['id']),
            'name': friend['name']
        })

    today = date.today()

    past_days = []
    today_day = None
    upcoming_days = []

    for day in days:
        # Convert day["date"] to date object if it's a string, or keep as is if it's already a date
        if isinstance(day["date"], str):
            day_date = date.fromisoformat(day["date"])
        else:
            day_date = day["date"]
            
        if day_date < today:
            past_days.append(day)
        elif day_date == today:
            today_day = day
        else:
            upcoming_days.append(day)

    return render_template(
        "trip.html",
        trip=trip,
        past_days=past_days,
        today_day=today_day,
        upcoming_days=upcoming_days,
        members=members,
        friends=friends_with_public_ids
    )

@app.route("/trip/<trip_id>/day/<day_id>")
@login_required
def day_view(trip_id, day_id):
    conn = get_db()

    # Check if user is owner or member of the trip
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT t.*
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.id = %s AND (t.owner_id = %s OR tm.user_id = %s)
    """, (trip_id, g.current_user["id"], g.current_user["id"]))
    trip = cur.fetchone()
    cur.close()

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM days WHERE id = %s AND trip_id = %s",
        (day_id, trip_id)
    )
    day = cur.fetchone()
    cur.close()

    if not trip or not day:
        return "Not found", 404

    # Get trip members
    cur = conn.cursor()
    cur.execute("""
        SELECT tm.user_id, tm.role, tm.joined_at, u.name
        FROM trip_members tm
        JOIN users u ON tm.user_id = u.id
        WHERE tm.trip_id = %s
        ORDER BY tm.role DESC, tm.joined_at ASC
    """, (trip_id,))
    members = cur.fetchall()
    cur.close()

    # ensure transport groups exist for this day
    ensure_transport_groups(trip_id, day_id)

    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM tasks
        WHERE day_id = %s AND (is_deleted IS NULL OR is_deleted = false)
        ORDER BY order_index ASC
    """, (day_id,))
    tasks = cur.fetchall()
    cur.close()

    # Get task status from task_status_events
    task_statuses = {}
    if tasks:
        task_ids = [task['id'] for task in tasks]
        cur = conn.cursor()
        cur.execute(f"""
            SELECT DISTINCT task_id, status
            FROM task_status_events
            WHERE task_id IN ({','.join(['%s' for _ in task_ids])})
            AND responded_at = (
                SELECT MAX(responded_at) 
                FROM task_status_events tse2 
                WHERE tse2.task_id = task_status_events.task_id
            )
        """, task_ids)
        status_events = cur.fetchall()
        cur.close()
        
        for event in status_events:
            task_statuses[event['task_id']] = event['status']

    now = datetime.now()

    # compute today flag and lateness info
    today_str = date.today().isoformat()
    active_groups = get_active_transport_groups(trip_id, day_id)

    processed_tasks = []
    for task in tasks:
        # Convert day["date"] to string for comparison if it's a date object
        if isinstance(day["date"], str):
            day_date_str = day["date"]
        else:
            day_date_str = day["date"].isoformat()
            
        start_dt = datetime.strptime(
            f"{day_date_str} {task['start_time']}",
            "%Y-%m-%d %H:%M"
        )

        is_past = now > (start_dt + timedelta(hours=4))

        is_today = (day_date_str == today_str)

        # default
        late_minutes = 0

        if is_today:
            lateness_vals = []
            for group in active_groups:
                eta = calculate_eta(group['group'], task)
                if eta:
                    _, eta_minutes = eta
                    lm = lateness_minutes(task, eta_minutes)
                    lateness_vals.append(lm)

            if lateness_vals:
                # choose the smallest positive lateness (if any), else 0
                positive = [v for v in lateness_vals if v > 0]
                late_minutes = min(positive) if positive else 0

        # Check task status from events
        task_status = task_statuses.get(task['id'], None)
        is_completed = (task_status == 'YES')
        is_skipped = (task_status == 'SKIPPED')

        # format status_updated_at for display
        status_ts = dict(task).get("status_updated_at")
        status_display = None
        if status_ts:
            try:
                status_dt = datetime.fromisoformat(status_ts)
                status_display = status_dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                status_display = status_ts

        processed_tasks.append({
            **task,
            "is_past": is_past,
            "is_today": is_today,
            "late_minutes": late_minutes,
            "status_updated_at": status_display,
            "completed": is_completed,
            "skipped": is_skipped,
            "status": task_status
        })

    return render_template(
        "day.html",
        trip=trip,
        day=day,
        tasks=processed_tasks,
        active_groups=active_groups
    )


def get_active_transport_groups(trip_id, day_id):
    """Get active transport groups for a specific trip and day"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT * FROM transport_groups
        WHERE trip_id = %s AND day_id = %s
    """, (trip_id, day_id))
    
    groups = cur.fetchall()
    cur.close()
    
    # Format groups for the calling code
    active_groups = []
    for group in groups:
        active_groups.append({
            'group': group
        })
    
    return active_groups


def ensure_transport_groups(trip_id, day_id):
    conn = get_db()

    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM transport_groups
        WHERE trip_id = %s AND day_id = %s
    """, (trip_id, day_id))
    groups = cur.fetchall()
    cur.close()

    if groups:
        return

    # create default group
    group_id = uid()
    now = datetime.now().isoformat()

    cur = conn.cursor()
    cur.execute("""
        SELECT user_id FROM trip_members
        WHERE trip_id = %s AND role = 'owner'
    """, (trip_id,))
    owner = cur.fetchone()
    cur.close()

    leader_id = owner["user_id"]

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transport_groups
        (id, trip_id, day_id, task_id, mode_id, label, leader_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        group_id,
        trip_id,
        day_id,
        None,
        "walk",
        None,
        leader_id,
        now
    ))
    cur.close()

    cur = conn.cursor()
    cur.execute("""
        SELECT user_id FROM trip_members
        WHERE trip_id = %s
    """, (trip_id,))
    members = cur.fetchall()
    cur.close()

    for m in members:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transport_group_members
            (transport_group_id, user_id, effective_mode_id)
            VALUES (%s, %s, %s)
        """, (
            group_id,
            m["user_id"],
            None
        ))
        cur.close()

    conn.commit()

    conn = get_db()

    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM transport_groups
        WHERE trip_id = %s AND day_id = %s
    """, (trip_id, day_id))
    groups = cur.fetchall()
    cur.close()

    result = []

    for group in groups:
        cur = conn.cursor()
        cur.execute("""
            SELECT user_id FROM transport_group_members
            WHERE transport_group_id = %s
        """, (group["id"],))
        members = cur.fetchall()
        cur.close()

        result.append({
            "group": group,
            "members": members
        })

    return result


def regroup_transport(trip_id, day_id, groups_payload):
    """
    groups_payload example:
    [
      {"mode": "car", "leader": "u1", "members": ["u1","u2"]},
      {"mode": "bike", "leader": "u3", "members": ["u3","u4"]}
    ]
    """
    conn = get_db()
    now = datetime.now().isoformat()

    # remove old memberships for this day's groups
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM transport_group_members
        WHERE transport_group_id IN (
            SELECT id FROM transport_groups
            WHERE trip_id = %s AND day_id = %s
        )
    """, (trip_id, day_id))
    cur.close()

    for group_data in groups_payload:
        gid = uid()

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transport_groups
            (id, trip_id, day_id, task_id, mode_id, label, leader_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            gid,
            trip_id,
            day_id,
            None,
            group_data["mode"],
            None,
            group_data["leader"],
            now
        ))
        cur.close()

        for u in group_data["members"]:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO transport_group_members
                (transport_group_id, user_id, effective_mode_id)
                VALUES (%s, %s, %s)
            """, (gid, u, None))
            cur.close()

    conn.commit()


# ------------------ Phase 3.3: Distance & ETA engine ------------------

MODE_SPEED_KMPH = {
    "walk": 5,
    "bike": 35,
    "car": 50,
    "bus": 40,
    "train": 80,
    "flight": 600,
}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in KM

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def record_location(user_id, group_id, lat, lng):
    conn = get_db()
    now = datetime.now().isoformat()

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO location_updates
        (id, user_id, transport_group_id, lat, lng, recorded_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        uid(),
        user_id,
        group_id,
        lat,
        lng,
        now
    ))
    cur.close()
    conn.commit()


def get_last_location(group_id):
    conn = get_db()

    cur = conn.cursor()
    cur.execute("""
        SELECT lat, lng FROM location_updates
        WHERE transport_group_id = %s
        ORDER BY recorded_at DESC
        LIMIT 1
    """, (group_id,))
    loc = cur.fetchone()
    cur.close()

    return loc


def calculate_eta(group, task):
    """
    group: transport_groups row
    task: tasks row (must have lat, lng, start_time)
    """
    last_loc = get_last_location(group["id"])

    if not last_loc or not dict(task).get("lat") or not dict(task).get("lng"):
        return None

    distance_km = haversine_km(
        last_loc["lat"],
        last_loc["lng"],
        task["lat"],
        task["lng"]
    )

    speed = MODE_SPEED_KMPH.get(group.get("mode_id") or group.get("mode") , 30)
    eta_minutes = int((distance_km / speed) * 60)

    return distance_km, eta_minutes


def save_eta_snapshot(group_id, task_id, distance_km, eta_minutes):
    conn = get_db()
    now = datetime.now().isoformat()

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO eta_snapshots
        (id, group_id, task_id, distance_km, eta_minutes, calculated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        uid(),
        group_id,
        task_id,
        distance_km,
        eta_minutes,
        now
    ))
    cur.close()
    conn.commit()


def lateness_minutes(task, eta_minutes):
    # task may not include date directly; attempt to use task['date'] else fetch day
    task_date = task.get("date")

    if not task_date:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM days WHERE id = %s", (task["day_id"],)
        )
        day = cur.fetchone()
        cur.close()
        task_date = day["date"] if day else None

    if not task_date:
        return 0

    # Convert task_date to string if it's a date object
    if isinstance(task_date, str):
        task_date_str = task_date
    else:
        task_date_str = task_date.isoformat()

    task_time = datetime.strptime(
        f"{task_date_str} {task['start_time']}",
        "%Y-%m-%d %H:%M"
    )

    arrival_time = datetime.now() + timedelta(minutes=eta_minutes)

    if arrival_time <= task_time:
        return 0

    return int((arrival_time - task_time).total_seconds() / 60)


@app.route("/task/<task_id>/arrive/<decision>")
def arrive_decision(task_id, decision):
    if decision not in ("YES", "NO", "SKIPPED"):
        return "Invalid decision", 400

    conn = get_db()
    now = datetime.now().isoformat()

    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE id = %s",
        (task_id,)
    )
    task = cur.fetchone()
    cur.close()

    if not task:
        return "Task not found", 404

    # Record event (history)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO task_status_events
        (id, task_id, user_id, status, responded_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        uid(),
        task_id,
        "user_1",
        decision,
        now
    ))
    cur.close()

    # Update current task status
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks
        SET status = %s, status_updated_at = %s
        WHERE id = %s
    """, (
        decision,
        now,
        task_id
    ))
    cur.close()
    conn.commit()

    conn.commit()

    return redirect(
        url_for(
            "day_view",
            trip_id=task["trip_id"],
            day_id=task["day_id"]
        )
    )


@app.route("/user/<user_id>")
def user_profile(user_id):
    # placeholder for user profile
    return f"User: {user_id}"

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth"))

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return empty response with no content status

@app.route("/trip/<trip_id>/day/<day_id>/add-task", methods=["GET", "POST"])
@login_required
def add_task_to_day(trip_id, day_id):
    conn = get_db()
    
    # Get trip and day info - allow owners and members
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT t.*
        FROM trips t
        LEFT JOIN trip_members tm ON t.id = tm.trip_id
        WHERE t.id = %s AND (t.owner_id = %s OR tm.user_id = %s)
    """, (trip_id, g.current_user["id"], g.current_user["id"]))
    trip = cur.fetchone()
    cur.close()
    
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM days WHERE id = %s AND trip_id = %s", (day_id, trip_id)
    )
    day = cur.fetchone()
    cur.close()
    
    if not trip or not day:
        flash("Trip or day not found", "error")
        return redirect(url_for("trips"))
    
    if request.method == "POST":
        title = request.form.get("title")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        description = request.form.get("description", "")
        lat = request.form.get("lat")
        lng = request.form.get("lng")
        
        if not title or not start_time or not end_time:
            flash("Title, start time, and end time are required", "error")
            return redirect(request.url)
        
        # Convert lat/lng to float if provided
        try:
            lat = float(lat) if lat and lat.strip() else None
            lng = float(lng) if lng and lng.strip() else None
        except (ValueError, TypeError):
            lat = None
            lng = None
        
        # Get the next order index
        cur = conn.cursor()
        cur.execute(
            "SELECT MAX(order_index) as max_order FROM tasks WHERE day_id = %s", (day_id,)
        )
        result = cur.fetchone()
        last_order = result['max_order'] if result and result['max_order'] is not None else 0
        cur.close()
        order_index = last_order + 1
        
        # Create the task
        task_id = uid()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tasks (id, trip_id, day_id, title, description, start_time, end_time, lat, lng, order_index, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (task_id, trip_id, day_id, title, description, start_time, end_time, lat, lng, order_index, datetime.now().isoformat())
        )
        cur.close()
        conn.commit()
        
        flash("Task added successfully!", "success")
        return redirect(url_for("day_view", trip_id=trip_id, day_id=day_id))
    
    return render_template("add_task.html", trip=trip, day=day)

if __name__ == "__main__":
    with app.app_context():
        # Test connection speed before starting server
        print(">>> Testing database connection speed...")
        from db import test_connection_speed
        connection_result = test_connection_speed()
        
        if connection_result is None:
            print(">>> ⚠️  Database connection test failed, but continuing to start server...")
            print(">>> 🔄 The app may still work if database connectivity improves")
        
        try:
            # Initialize the database
            print(">>> Initializing database...")
            init_db()
            
            # Ensure is_deleted column exists for tasks
            conn = get_db()
            try:
                cur = conn.cursor()
                cur.execute("ALTER TABLE tasks ADD COLUMN is_deleted INTEGER DEFAULT 0")
                cur.close()
                conn.commit()
                print("Added is_deleted column to tasks table")
            except:
                pass  # Column already exists
                
        except Exception as e:
            print(f">>> ⚠️  Database initialization failed: {e}")
            print(">>> 🔄 Server will start anyway - try accessing the app to trigger reconnection")
    
    print(">>> Starting Flask server with optimized settings...")
    # Optimize Flask development server for better performance on Windows
    app.run(
        debug=True,
        threaded=True,           # Enable multithreading to reduce blocking
        host='127.0.0.1',       # Force IPv4 localhost (faster than 'localhost')
        port=5000,
        use_reloader=True,
        use_debugger=True,
        # Additional optimizations
        processes=1,            # Single process but multi-threaded
        request_handler=None,   # Use default Werkzeug handler (optimized)
    )
