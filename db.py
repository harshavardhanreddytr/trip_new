import os
import time
import socket
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import g

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable not set")

# Generate unpooled connection URL for fallback
def get_unpooled_url(pooled_url):
    """Convert pooled Neon URL to unpooled for better dev performance"""
    if '-pooler.' in pooled_url:
        return pooled_url.replace('-pooler.', '.')
    return pooled_url

UNPOOLED_DATABASE_URL = get_unpooled_url(DATABASE_URL)
USE_UNPOOLED = False  # Will be set based on connection speed test

# Windows-specific network optimizations
def optimize_for_windows():
    """Apply Windows-specific socket and DNS optimizations"""
    try:
        # Aggressive IPv4-first DNS resolution to avoid slow IPv6 lookups on Windows
        original_getaddrinfo = socket.getaddrinfo
        def fast_ipv4_getaddrinfo(host, port, family=0, socktype=0, proto=0, flags=0):
            # Force IPv4 first, with very short timeout for IPv6 fallback
            try:
                # Try IPv4 with AI_ADDRCONFIG to use only configured address families
                return original_getaddrinfo(host, port, socket.AF_INET, socktype, proto, socket.AI_ADDRCONFIG)
            except (socket.gaierror, OSError):
                # Quick fallback to default resolution
                return original_getaddrinfo(host, port, family, socktype, proto, flags)
        
        socket.getaddrinfo = fast_ipv4_getaddrinfo
        
        # Additional socket optimizations for Windows
        if hasattr(socket, 'TCP_NODELAY'):
            socket.TCP_NODELAY = 1
        if hasattr(socket, 'SO_KEEPALIVE'):
            socket.SO_KEEPALIVE = 1
            
        print(">>> Applied Windows IPv4-first DNS optimization")
        
    except Exception as e:
        print(f">>> Network optimization warning: {e}")

# Apply optimizations immediately
optimize_for_windows()

print(">>> Using PostgreSQL database with Windows network optimizations")
if '-pooler.' in DATABASE_URL:
    print(">>> Pooled connection available:", DATABASE_URL.split('@')[1].split('/')[0])
    print(">>> Unpooled fallback available:", UNPOOLED_DATABASE_URL.split('@')[1].split('/')[0])
else:
    print(">>> Direct connection:", DATABASE_URL.split('@')[1].split('/')[0])

# Add connection health check function
def test_connection_speed():
    """Test database connection speed and auto-switch to unpooled if needed"""
    global USE_UNPOOLED
    
    try:
        # Test pooled connection first with longer timeout for initial connection
        print(">>> Testing pooled connection...")
        start = time.time()
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor,
            connect_timeout=15  # Increased from 5 to 15 seconds
        )
        conn.close()
        pooled_speed = (time.time() - start) * 1000
        print(f">>> Pooled connection: {pooled_speed:.1f}ms")
        
        # If pooled is too slow and we have an unpooled option, test it
        if pooled_speed > 800 and UNPOOLED_DATABASE_URL != DATABASE_URL:
            print(">>> Testing unpooled connection...")
            start = time.time()
            conn = psycopg2.connect(
                UNPOOLED_DATABASE_URL,
                cursor_factory=RealDictCursor,
                connect_timeout=15  # Increased from 5 to 15 seconds
            )
            conn.close()
            unpooled_speed = (time.time() - start) * 1000
            print(f">>> Unpooled connection: {unpooled_speed:.1f}ms")
            
            # Auto-switch if unpooled is significantly faster
            improvement = (pooled_speed - unpooled_speed) / pooled_speed * 100
            if unpooled_speed < pooled_speed * 0.90:  # 10% improvement threshold
                USE_UNPOOLED = True
                print(f">>> 🚀 AUTO-SWITCHING to unpooled connection ({improvement:.1f}% faster: {unpooled_speed:.1f}ms vs {pooled_speed:.1f}ms)")
                return unpooled_speed
            else:
                print(f">>> Staying with pooled connection (unpooled only {improvement:.1f}% faster)")
        
        if pooled_speed > 1000:
            print(f">>> ⚠️  Connection: {pooled_speed:.1f}ms - Very slow, consider network optimization")
        elif pooled_speed > 500:
            print(f">>> 🔶 Connection: {pooled_speed:.1f}ms - Moderate latency detected")
        else:
            print(f">>> ✅ Connection: {pooled_speed:.1f}ms - Good performance")
            
        return pooled_speed
        
    except psycopg2.OperationalError as e:
        if "timeout expired" in str(e):
            print(f">>> ❌ Database connection timeout: Network connectivity issues detected")
            print(f">>> 💡 Try: Check internet connection, VPN, or firewall settings")
        else:
            print(f">>> ❌ Database connection failed: {e}")
        print(f">>> 🔄 Attempting to continue without speed test...")
        return None
    except Exception as e:
        print(f">>> ❌ Connection test failed: {e}")
        return None

def get_active_database_url():
    """Get the currently active database URL (pooled or unpooled)"""
    return UNPOOLED_DATABASE_URL if USE_UNPOOLED else DATABASE_URL


def get_db():
    # Try to use g for connection reuse within request context
    try:
        if "db_conn" not in g:
            # Measure connection time with retry logic
            max_retries = 2
            retry_count = 0
            
            while retry_count <= max_retries:
                start_time = time.time()
                
                try:
                    # Use the optimal database URL (pooled or unpooled)
                    active_url = get_active_database_url()
                    connection_params = {
                        'dsn': active_url,
                        'cursor_factory': RealDictCursor,
                        # Realistic timeout for current network conditions
                        'connect_timeout': 5,
                        'application_name': f'tripplanner_flask_r{retry_count}',
                        # Simplified keepalive settings
                        'keepalives': 1,
                    }
                    
                    g.db_conn = psycopg2.connect(**connection_params)
                    g.db_conn.autocommit = True  # Enable autocommit for better performance
                    
                    connection_time = (time.time() - start_time) * 1000
                    
                    # Enhanced logging with retry info
                    retry_suffix = f" (retry {retry_count})" if retry_count > 0 else ""
                    conn_type = "unpooled" if USE_UNPOOLED else "pooled"
                    if connection_time > 1000:  # Very slow (>1 second)
                        print(f">>> 🐌 VERY SLOW DB CONNECTION: {connection_time:.1f}ms{retry_suffix} ({conn_type}) - Network issue!")
                    elif connection_time > 200:  # Slow  
                        print(f">>> 🔶 SLOW DB CONNECTION: {connection_time:.1f}ms{retry_suffix} ({conn_type}) - High latency")
                    elif connection_time > 50:   # Moderate
                        print(f">>> 🔸 DB connection: {connection_time:.1f}ms{retry_suffix} ({conn_type})")
                    else:
                        print(f">>> ✅ Fast DB connection: {connection_time:.1f}ms{retry_suffix} ({conn_type})")
                    
                    break  # Success, exit retry loop
                    
                except (psycopg2.OperationalError, psycopg2.DatabaseError) as e:
                    retry_count += 1
                    connection_time = (time.time() - start_time) * 1000
                    
                    if retry_count > max_retries:
                        print(f">>> ❌ DB CONNECTION FAILED after {max_retries} retries: {e}")
                        raise  # Re-raise the last exception
                    else:
                        print(f">>> 🔄 DB connection retry {retry_count}/{max_retries} (failed in {connection_time:.1f}ms): {str(e)[:100]}...")
                        time.sleep(0.1 * retry_count)  # Brief exponential backoff
                
        return g.db_conn
        
    except RuntimeError:
        # Outside application context (e.g., init_db)
        start_time = time.time()
        active_url = get_active_database_url()
        conn = psycopg2.connect(
            active_url,
            cursor_factory=RealDictCursor,
            connect_timeout=5,
            keepalives=1,
        )
        conn.autocommit = True
        
        connection_time = (time.time() - start_time) * 1000
        conn_type = "unpooled" if USE_UNPOOLED else "pooled"
        if connection_time > 1000:
            print(f">>> 🐌 Init DB connection (very slow): {connection_time:.1f}ms ({conn_type})")
        elif connection_time > 200:
            print(f">>> 🔶 Init DB connection (slow): {connection_time:.1f}ms ({conn_type})")
        else:
            print(f">>> Init DB connection: {connection_time:.1f}ms ({conn_type})")
        return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    # ---------------- USERS ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            password TEXT,
            email TEXT UNIQUE,
            created_at TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            user_id TEXT,
            friend_id TEXT,
            created_at TIMESTAMP,
            PRIMARY KEY (user_id, friend_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS friend_requests (
            id TEXT PRIMARY KEY,
            sender_id TEXT,
            receiver_id TEXT,
            message TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP,
            responded_at TIMESTAMP
        )
    """)

    # ---------------- TRIPS ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            name TEXT,
            start_date DATE,
            end_date DATE,
            owner_id TEXT,
            created_at TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trip_members (
            trip_id TEXT,
            user_id TEXT,
            role TEXT,
            joined_at TEXT,
            left_at TEXT,
            PRIMARY KEY (trip_id, user_id)
        )
    """)

    # ---------------- DAYS ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS days (
            id TEXT PRIMARY KEY,
            trip_id TEXT,
            date DATE
        )
    """)

    # ---------------- TASKS ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            trip_id TEXT,
            day_id TEXT,
            title TEXT,
            description TEXT,
            start_time TEXT,
            end_time TEXT,
            lat REAL,
            lng REAL,
            order_index REAL,
            created_at TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_assignments (
            task_id TEXT,
            user_id TEXT,
            required BOOLEAN,
            PRIMARY KEY (task_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_status_events (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            user_id TEXT,
            status TEXT,
            responded_at TIMESTAMP
        )
    """)

    # ---------------- TRANSPORT ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transport_modes (
            id TEXT PRIMARY KEY,
            name TEXT,
            avg_speed REAL,
            buffer_minutes INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transport_groups (
            id TEXT PRIMARY KEY,
            trip_id TEXT,
            day_id TEXT,
            task_id TEXT,
            mode_id TEXT,
            label TEXT,
            leader_id TEXT,
            created_at TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transport_group_members (
            transport_group_id TEXT,
            user_id TEXT,
            effective_mode_id TEXT,
            PRIMARY KEY (transport_group_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS eta_snapshots (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            user_id TEXT,
            eta_minutes INTEGER,
            created_at TIMESTAMP
        )
    """)

    # ---------------- LOCATION ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS location_updates (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            transport_group_id TEXT,
            lat REAL,
            lng REAL,
            recorded_at TIMESTAMP
        )
    """)

    # ---------------- NOTES ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_notes (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            current_text TEXT,
            updated_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_note_history (
            id TEXT PRIMARY KEY,
            note_id TEXT,
            text TEXT,
            edited_by TEXT,
            edited_at TIMESTAMP
        )
    """)

    # ---------------- CHAT ----------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_threads (
            id TEXT PRIMARY KEY,
            trip_id TEXT,
            task_id TEXT,
            created_at TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            thread_id TEXT,
            sender_id TEXT,
            message TEXT,
            message_type TEXT,
            created_at TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
