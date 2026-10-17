import os
import json
import sqlite3
import re
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

# Default Departments from app.sql
DEFAULT_DEPARTMENTS = [
    'Computer Engineering',
    'Computer Science and Engineering',
    'Information Technology',
    'Artificial Intelligence and Machine Learning',
    'Artificial Intelligence and Data Science',
    'Data Science',
    'Electronics and Telecommunication Engineering',
    'Electronics Engineering',
    'Electrical Engineering',
    'Mechanical Engineering',
    'Civil Engineering',
    'Chemical Engineering',
    'Instrumentation Engineering',
    'Production Engineering',
    'Automobile Engineering',
    'Robotics and Automation',
    'Mechatronics Engineering',
    'Biotechnology Engineering',
    'Biomedical Engineering',
    'Aerospace Engineering',
    'Other'
]

# Database configuration parameters
DB_NAME = os.environ.get('DB_NAME', 'catalyst_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', os.environ.get('DB_PASS', 'postgres'))
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

_USE_SQLITE_FALLBACK = False
_sqlite_conn = None

PROF_NUM_TO_STR = {
    '1': 'Beginner', '2': 'Intermediate', '3': 'Proficient', '4': 'Advanced', '5': 'Expert',
    1: 'Beginner', 2: 'Intermediate', 3: 'Proficient', 4: 'Advanced', 5: 'Expert',
    'beginner': 'Beginner', 'intermediate': 'Intermediate', 'proficient': 'Proficient',
    'advanced': 'Advanced', 'expert': 'Expert',
    'Beginner': 'Beginner', 'Intermediate': 'Intermediate', 'Proficient': 'Proficient',
    'Advanced': 'Advanced', 'Expert': 'Expert'
}

PROF_STR_TO_NUM = {
    'Beginner': 1, 'Intermediate': 2, 'Proficient': 3, 'Advanced': 4, 'Expert': 5,
    'beginner': 1, 'intermediate': 2, 'proficient': 3, 'advanced': 4, 'expert': 5,
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5
}


# ============================================================
# CONNECTION HELPERS
# ============================================================

def get_connection():
    """Tries connecting to PostgreSQL catalyst_db; falls back to SQLite if PG connection fails."""
    global _USE_SQLITE_FALLBACK
    if _USE_SQLITE_FALLBACK:
        return None

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=3
        )
        return conn
    except Exception as e:
        if not _USE_SQLITE_FALLBACK:
            print(f"⚠️ PostgreSQL Connection Warning: {e}")
            print("🔄 Falling back to catalyst SQLite engine for smooth execution...")
            _USE_SQLITE_FALLBACK = True
            init_sqlite_fallback()
        return None


def _pg_or_sqlite(sql_pg, sql_sqlite, params_pg=(), params_sqlite=None, fetchall=True, fetchone=False):
    """
    Helper: tries PostgreSQL first, falls back to SQLite.
    Returns list of dicts (fetchall) or single dict (fetchone) or None.
    """
    if params_sqlite is None:
        params_sqlite = params_pg

    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql_pg, params_pg)
                if fetchone:
                    row = cur.fetchone()
                    conn.close()
                    return dict(row) if row else None
                rows = cur.fetchall()
                conn.close()
                return [dict(r) for r in rows]
        except Exception as err:
            print(f"PG query error: {err}")
            conn.close()

    # SQLite fallback
    cursor = _sqlite_conn.cursor()
    cursor.execute(sql_sqlite, params_sqlite)
    if fetchone:
        row = cursor.fetchone()
        return dict(row) if row else None
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


# ============================================================
# SCHEMA MIGRATION & SEEDING
# ============================================================

def seed_from_app_sql():
    """Seeds database (PostgreSQL or SQLite fallback) from app.sql if students table is empty."""
    sql_file = os.path.join(os.path.dirname(__file__), 'app.sql')
    if not os.path.exists(sql_file):
        return

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_text = f.read()

    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT COUNT(*) FROM students;")
                    cnt = cur.fetchone()[0]
                    if cnt > 0:
                        conn.close()
                        return
                except Exception:
                    pass
                
                print("🌱 Seeding PostgreSQL database from app.sql...")
                cur.execute(sql_text)
            conn.commit()
            print("✅ PostgreSQL database successfully seeded from app.sql!")
        except Exception as e:
            print(f"PG app.sql seeding note: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    else:
        global _sqlite_conn
        if _sqlite_conn is None:
            return

        try:
            cursor = _sqlite_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM students;")
            cnt = cursor.fetchone()[0]
            if cnt > 0:
                return
        except Exception:
            pass

        print("🌱 Seeding SQLite database from app.sql...")
        sqlite_sql = re.sub(r'DROP TABLE IF EXISTS (\w+) CASCADE;', r'DROP TABLE IF EXISTS \1;', sql_text, flags=re.IGNORECASE)
        sqlite_sql = re.sub(r'\bSERIAL PRIMARY KEY\b', 'INTEGER PRIMARY KEY AUTOINCREMENT', sqlite_sql, flags=re.IGNORECASE)
        sqlite_sql = re.sub(r'\bBOOLEAN\b', 'INTEGER', sqlite_sql, flags=re.IGNORECASE)
        sqlite_sql = re.sub(r'\bTRUE\b', '1', sqlite_sql, flags=re.IGNORECASE)
        sqlite_sql = re.sub(r'\bFALSE\b', '0', sqlite_sql, flags=re.IGNORECASE)

        statements = [s.strip() for s in sqlite_sql.split(';') if s.strip()]
        cursor = _sqlite_conn.cursor()
        for stmt in statements:
            if stmt.upper().startswith('CREATE OR REPLACE VIEW') or (stmt.upper().startswith('SELECT') and not 'INTO' in stmt.upper()):
                continue
            try:
                cursor.execute(stmt)
            except Exception:
                pass
        _sqlite_conn.commit()
        print("⚡ SQLite database successfully seeded from app.sql!")


def ensure_pg_schema():
    """Adds any missing columns / tables to the existing PostgreSQL schema (safe to run multiple times)."""
    conn = get_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE;")
            # student_pitch table (may not exist if running against older DB)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS student_pitch (
                    pitch_id SERIAL PRIMARY KEY,
                    student_id INTEGER UNIQUE NOT NULL,
                    answer TEXT NOT NULL,
                    word_count INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
                );
            ''')
            # Marksheets and card completion columns
            cur.execute("ALTER TABLE academic_records ADD COLUMN IF NOT EXISTS marksheet_10th_path TEXT;")
            cur.execute("ALTER TABLE academic_records ADD COLUMN IF NOT EXISTS marksheet_12th_path TEXT;")
            cur.execute("ALTER TABLE academic_records ADD COLUMN IF NOT EXISTS marksheet_sems_json TEXT;")
            cur.execute("ALTER TABLE research_papers ADD COLUMN IF NOT EXISTS has_published INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE research_papers ALTER COLUMN paper_title DROP NOT NULL;")
            cur.execute("ALTER TABLE internships ADD COLUMN IF NOT EXISTS has_internship INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE internships ALTER COLUMN company_name DROP NOT NULL;")
            cur.execute("ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS has_hackathon INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE hackathons ALTER COLUMN hackathon_name DROP NOT NULL;")
            cur.execute("ALTER TABLE courses_certificates ADD COLUMN IF NOT EXISTS has_certificate INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE courses_certificates ALTER COLUMN course_name DROP NOT NULL;")
            cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS has_project INTEGER DEFAULT 0;")
            cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS languages_json TEXT;")
            cur.execute("ALTER TABLE projects ALTER COLUMN project_title DROP NOT NULL;")
        conn.commit()
    except Exception as e:
        print(f"Schema migration note: {e}")
        conn.rollback()
    finally:
        conn.close()

    seed_from_app_sql()


def seed_pg_admins():
    """Seeds TPC admin credentials into PostgreSQL if not already present."""
    conn = get_connection()
    if not conn:
        return
    tpc_admins = [
        ('TPC101', 'aaaa', 'Rishikesh Yeolekar', 'tpc101@mmcoe.edu.in', 'Placement Coordinator'),
        ('TPC102', 'bbbb', 'Ashvini Ahirrao', 'tpc102@mmcoe.edu.in', 'Placement Coordinator'),
        ('TPC103', 'cccc', 'Avani Anawardekar', 'tpc103@mmcoe.edu.in', 'Placement Coordinator'),
        ('TPC104', 'dddd', 'Deepali Bhaturkar', 'tpc104@mmcoe.edu.in', 'Placement Coordinator'),
    ]
    try:
        with conn.cursor() as cur:
            for username, password, full_name, email, role in tpc_admins:
                cur.execute('''
                    INSERT INTO admins (username, password, full_name, email, role)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING;
                ''', (username, password, full_name, email, role))
        conn.commit()
        print("✅ TPC admin credentials seeded into PostgreSQL.")
    except Exception as e:
        print(f"Admin seeding note: {e}")
        conn.rollback()
    finally:
        conn.close()


# ============================================================
# SQLITE FALLBACK (only used when PostgreSQL is unavailable)
# ============================================================

def ensure_sqlite_schema(conn):
    """Ensures all necessary columns and tables exist in SQLite fallback database."""
    cursor = conn.cursor()

    def add_col_if_missing(table, col, col_def):
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cursor.fetchall()]
            if cols and col not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
        except Exception as e:
            print(f"Note adding {col} to {table}: {e}")

    add_col_if_missing('academic_records', 'marksheet_10th_path', 'TEXT')
    add_col_if_missing('academic_records', 'marksheet_12th_path', 'TEXT')
    add_col_if_missing('academic_records', 'marksheet_sems_json', 'TEXT')

    add_col_if_missing('research_papers', 'has_published', 'INTEGER DEFAULT 0')
    add_col_if_missing('internships', 'has_internship', 'INTEGER DEFAULT 0')
    add_col_if_missing('hackathons', 'has_hackathon', 'INTEGER DEFAULT 0')
    add_col_if_missing('courses_certificates', 'has_certificate', 'INTEGER DEFAULT 0')
    add_col_if_missing('projects', 'has_project', 'INTEGER DEFAULT 0')
    add_col_if_missing('projects', 'languages_json', 'TEXT')

    conn.commit()


def init_sqlite_fallback():
    """Initializes a persistent disk-backed SQLite database (catalyst.db) with schema & defaults if PostgreSQL is unavailable."""
    global _sqlite_conn
    if _sqlite_conn is not None:
        ensure_sqlite_schema(_sqlite_conn)
        return
    db_path = os.path.join(os.path.dirname(__file__), 'catalyst.db')
    _sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
    _sqlite_conn.row_factory = sqlite3.Row
    cursor = _sqlite_conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS departments (
        department_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT UNIQUE NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL DEFAULT 'Placement Coordinator',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        prn TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        college TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        current_year TEXT NOT NULL,
        current_semester INTEGER NOT NULL,
        graduation_year INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (department_id) REFERENCES departments(department_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS academic_records (
        academic_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        percentage_10th REAL,
        percentage_12th REAL,
        semester_1_sgpa REAL,
        semester_2_sgpa REAL,
        semester_3_sgpa REAL,
        semester_4_sgpa REAL,
        semester_5_sgpa REAL,
        semester_6_sgpa REAL,
        semester_7_sgpa REAL,
        semester_8_sgpa REAL,
        previous_backlogs INTEGER DEFAULT 0,
        marksheet_10th_path TEXT,
        marksheet_12th_path TEXT,
        marksheet_sems_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS backlogs (
        backlog_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        academic_level TEXT NOT NULL,
        subject_name TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coding_languages (
        student_language_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        language_name TEXT NOT NULL,
        proficiency_level TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS technical_skills (
        student_skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        proficiency_level TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS coding_platforms (
        coding_platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        platform_name TEXT NOT NULL,
        profile_url TEXT,
        questions_solved INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS linkedin_profiles (
        linkedin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        uses_for_academic_purposes INTEGER NOT NULL DEFAULT 0,
        profile_url TEXT,
        number_of_posts INTEGER DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS research_papers (
        research_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        has_published INTEGER DEFAULT 0,
        paper_title TEXT,
        publication_name TEXT,
        publication_date TEXT,
        paper_url TEXT,
        document_path TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS internships (
        internship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        has_internship INTEGER DEFAULT 0,
        company_name TEXT,
        role TEXT,
        start_date TEXT,
        end_date TEXT,
        offer_letter_path TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hackathons (
        hackathon_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        has_hackathon INTEGER DEFAULT 0,
        hackathon_name TEXT,
        organizer TEXT,
        participation_date TEXT,
        position TEXT,
        certificate_path TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses_certificates (
        certificate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        has_certificate INTEGER DEFAULT 0,
        course_name TEXT,
        platform TEXT,
        completion_date TEXT,
        certificate_path TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS aptitude_skills (
        student_aptitude_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        proficiency_level TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS communication_skills (
        student_communication_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        proficiency_level TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS foreign_languages (
        student_foreign_language_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        language_name TEXT NOT NULL,
        proficiency_level TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        has_project INTEGER DEFAULT 0,
        project_title TEXT,
        github_url TEXT,
        project_description TEXT,
        languages_json TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_pitch (
        pitch_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        answer TEXT NOT NULL,
        word_count INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assessments (
        assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_score REAL NOT NULL,
        classification TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assessment_category_scores (
        category_score_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        category_score REAL NOT NULL,
        maximum_score REAL NOT NULL,
        weightage REAL NOT NULL,
        FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS skill_gaps (
        gap_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        current_value TEXT NOT NULL,
        target_value TEXT NOT NULL,
        gap_description TEXT NOT NULL,
        priority TEXT NOT NULL,
        FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS recommendations (
        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assessment_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        recommendation TEXT NOT NULL,
        priority TEXT NOT NULL,
        FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
    )''')

    for dept in DEFAULT_DEPARTMENTS:
        cursor.execute('INSERT OR IGNORE INTO departments (department_name) VALUES (?)', (dept,))

    tpc_admins = [
        ('TPC101', 'aaaa', 'Rishikesh Yeolekar', 'tpc101@mmcoe.edu.in', 'Placement Coordinator'),
        ('TPC102', 'bbbb', 'Ashvini Ahirrao', 'tpc102@mmcoe.edu.in', 'Placement Coordinator'),
        ('TPC103', 'cccc', 'Avani Anawardekar', 'tpc103@mmcoe.edu.in', 'Placement Coordinator'),
        ('TPC104', 'dddd', 'Deepali Bhaturkar', 'tpc104@mmcoe.edu.in', 'Placement Coordinator'),
    ]
    for username, password, full_name, email, role in tpc_admins:
        cursor.execute('''
        INSERT OR IGNORE INTO admins (username, password, full_name, email, role)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, password, full_name, email, role))

    _sqlite_conn.commit()
    print("⚡ catalyst_db SQLite Fallback Initialized successfully!")
    seed_from_app_sql()
    ensure_sqlite_schema(_sqlite_conn)


# ============================================================
# DEPARTMENTS
# ============================================================

def get_departments():
    """Retrieves list of all engineering departments."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT department_id, department_name FROM departments ORDER BY department_id ASC;')
                rows = cur.fetchall()
                conn.close()
                return [dict(r) for r in rows]
        except Exception as err:
            print(f"Error reading departments from PG: {err}")
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('SELECT department_id, department_name FROM departments ORDER BY department_id ASC')
    return [dict(r) for r in cursor.fetchall()]


# ============================================================
# STUDENT REGISTRATION & AUTH
# ============================================================

def register_student(prn, full_name, email, raw_password, college, department_id,
                     current_year, current_semester, graduation_year, username=None):
    """Registers a new student into the database."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT student_id FROM students WHERE prn = %s OR email = %s;', (prn, email))
                if cur.fetchone():
                    conn.close()
                    return False, "PRN or Email is already registered."
                if username:
                    cur.execute('SELECT student_id FROM students WHERE username = %s;', (username,))
                    if cur.fetchone():
                        conn.close()
                        return False, "Username is already taken. Please choose a different username."
                cur.execute('''
                    INSERT INTO students (prn, username, full_name, email, password, college, department_id,
                                         current_year, current_semester, graduation_year)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING student_id;
                ''', (prn, username, full_name, email, raw_password, college,
                      int(department_id), current_year, int(current_semester), int(graduation_year)))
                new_student = cur.fetchone()
                student_id = new_student['student_id']
                conn.commit()
                conn.close()
                return True, student_id
        except Exception as err:
            if conn:
                conn.rollback()
                conn.close()
            return False, f"Database error during registration: {str(err)}"

    # SQLite Fallback
    cursor = _sqlite_conn.cursor()
    cursor.execute('SELECT student_id FROM students WHERE prn = ? OR email = ?', (prn, email))
    if cursor.fetchone():
        return False, "PRN or Email is already registered."
    if username:
        cursor.execute('SELECT student_id FROM students WHERE username = ?', (username,))
        if cursor.fetchone():
            return False, "Username is already taken. Please choose a different username."
    try:
        cursor.execute('''
            INSERT INTO students (prn, username, full_name, email, password, college, department_id,
                                  current_year, current_semester, graduation_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (prn, username, full_name, email, raw_password, college,
              int(department_id), current_year, int(current_semester), int(graduation_year)))
        _sqlite_conn.commit()
        return True, cursor.lastrowid
    except Exception as err:
        return False, f"Database error: {str(err)}"


def authenticate_student(identifier, password):
    """Authenticates a student by username, PRN, or email and password."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT s.*, d.department_name
                    FROM students s
                    JOIN departments d ON s.department_id = d.department_id
                    WHERE s.username = %s OR s.prn = %s OR s.email = %s;
                ''', (identifier, identifier, identifier))
                student = cur.fetchone()
                conn.close()
                if student:
                    stored_pass = student['password']
                    if stored_pass == password or (stored_pass.startswith('pbkdf2:') and check_password_hash(stored_pass, password)):
                        return dict(student)
                return None
        except Exception as err:
            print(f"Error authenticating student: {err}")
            if conn:
                conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        SELECT s.*, d.department_name
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        WHERE s.username = ? OR s.prn = ? OR s.email = ?
    ''', (identifier, identifier, identifier))
    student = cursor.fetchone()
    if student:
        student_dict = dict(student)
        stored_pass = student_dict['password']
        if stored_pass == password or (stored_pass.startswith('pbkdf2:') and check_password_hash(stored_pass, password)):
            return student_dict
    return None


def authenticate_admin(username, password):
    """Authenticates an admin/faculty/placement coordinator by username and password."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('SELECT * FROM admins WHERE username = %s;', (username,))
                admin = cur.fetchone()
                conn.close()
                if admin:
                    stored_pass = admin['password']
                    if stored_pass == password or (stored_pass.startswith('pbkdf2:') and check_password_hash(stored_pass, password)):
                        return dict(admin)
                return None
        except Exception as err:
            print(f"Error authenticating admin: {err}")
            if conn:
                conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('SELECT * FROM admins WHERE username = ?', (username,))
    admin = cursor.fetchone()
    if admin:
        admin_dict = dict(admin)
        stored_pass = admin_dict['password']
        if stored_pass == password or (stored_pass.startswith('pbkdf2:') and check_password_hash(stored_pass, password)):
            return admin_dict
    return None


def get_student_by_id(student_id):
    """Retrieves student record by student_id."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT s.*, d.department_name
                    FROM students s
                    JOIN departments d ON s.department_id = d.department_id
                    WHERE s.student_id = %s;
                ''', (student_id,))
                student = cur.fetchone()
                conn.close()
                if student:
                    return dict(student)
        except Exception as err:
            print(f"Error getting student by ID: {err}")
            if conn:
                conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        SELECT s.*, d.department_name
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        WHERE s.student_id = ?
    ''', (student_id,))
    student = cursor.fetchone()
    return dict(student) if student else None


# ============================================================
# CARD DATA READ — PostgreSQL-aware
# ============================================================

def _pg_fetch_all(conn, sql, params=()):
    """Executes a SELECT on PG connection, returns list of dicts."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def _pg_fetch_one(conn, sql, params=()):
    """Executes a SELECT on PG connection, returns a single dict or None."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def get_student_card_data(student_id):
    """Retrieves current responses and completion status for all 13 cards."""
    conn = get_connection()
    using_pg = conn is not None

    try:
        if using_pg:
            # 1. Academics
            academics_dict = _pg_fetch_one(conn,
                'SELECT * FROM academic_records WHERE student_id = %s', (student_id,))
            backlogs_list = []
            if academics_dict:
                backlogs_list = _pg_fetch_all(conn,
                    'SELECT * FROM backlogs WHERE student_id = %s', (student_id,))

            # 2. Coding Languages — PG uses normalized table with language_id FK
            coding_langs = _pg_fetch_all(conn, '''
                SELECT cl.student_language_id, cl.student_id,
                       clm.language_name, cl.proficiency_level
                FROM coding_languages cl
                JOIN coding_language_master clm ON cl.language_id = clm.language_id
                WHERE cl.student_id = %s
            ''', (student_id,))

            # 3. Technical Skills — normalized with technical_skill_id FK
            tech_skills = _pg_fetch_all(conn, '''
                SELECT ts.student_skill_id, ts.student_id,
                       tsm.skill_name, ts.proficiency_level
                FROM technical_skills ts
                JOIN technical_skill_master tsm ON ts.technical_skill_id = tsm.technical_skill_id
                WHERE ts.student_id = %s
            ''', (student_id,))

            # 4. Coding Platforms — normalized with platform_id FK
            coding_platforms = _pg_fetch_all(conn, '''
                SELECT cp.coding_platform_id, cp.student_id,
                       cpm.platform_name, cp.profile_url, cp.questions_solved
                FROM coding_platforms cp
                JOIN coding_platform_master cpm ON cp.platform_id = cpm.platform_id
                WHERE cp.student_id = %s
            ''', (student_id,))

            # 5. LinkedIn
            linkedin = _pg_fetch_one(conn,
                'SELECT * FROM linkedin_profiles WHERE student_id = %s', (student_id,))

            # 6. Research Papers
            research_papers = _pg_fetch_all(conn,
                'SELECT * FROM research_papers WHERE student_id = %s', (student_id,))
            for p in research_papers:
                p['has_published'] = 1 if p.get('paper_title') else p.get('has_published', 0)

            # 7. Internships
            internships = _pg_fetch_all(conn,
                'SELECT * FROM internships WHERE student_id = %s', (student_id,))
            for i in internships:
                i['has_internship'] = 1 if i.get('company_name') else i.get('has_internship', 0)

            # 8. Hackathons
            hackathons = _pg_fetch_all(conn,
                'SELECT * FROM hackathons WHERE student_id = %s', (student_id,))
            for h in hackathons:
                h['has_hackathon'] = 1 if h.get('hackathon_name') else h.get('has_hackathon', 0)

            # 9. Courses and Certificates
            certificates = _pg_fetch_all(conn,
                'SELECT * FROM courses_certificates WHERE student_id = %s', (student_id,))
            for c in certificates:
                c['has_certificate'] = 1 if c.get('course_name') else c.get('has_certificate', 0)

            # 10. Aptitude Skills — normalized with aptitude_skill_id FK
            aptitude = _pg_fetch_all(conn, '''
                SELECT aps.student_aptitude_id, aps.student_id,
                       asm.skill_name, aps.proficiency_level
                FROM aptitude_skills aps
                JOIN aptitude_skill_master asm ON aps.aptitude_skill_id = asm.aptitude_skill_id
                WHERE aps.student_id = %s
            ''', (student_id,))

            # 11. Communication Skills — normalized with communication_skill_id FK
            communication = _pg_fetch_all(conn, '''
                SELECT cs.student_communication_id, cs.student_id,
                       csm.skill_name, cs.proficiency_level
                FROM communication_skills cs
                JOIN communication_skill_master csm ON cs.communication_skill_id = csm.communication_skill_id
                WHERE cs.student_id = %s
            ''', (student_id,))

            # 12. Foreign Languages — normalized with foreign_language_id FK
            foreign_langs = _pg_fetch_all(conn, '''
                SELECT fl.student_foreign_language_id, fl.student_id,
                       flm.language_name, fl.proficiency_level
                FROM foreign_languages fl
                JOIN foreign_language_master flm ON fl.foreign_language_id = flm.foreign_language_id
                WHERE fl.student_id = %s
            ''', (student_id,))

            # 13. Projects — PG has separate project_languages table; flatten into languages_json
            projects_raw = _pg_fetch_all(conn,
                'SELECT * FROM projects WHERE student_id = %s', (student_id,))
            projects = []
            for proj in projects_raw:
                proj['has_project'] = 1 if proj.get('project_title') else proj.get('has_project', 0)
                # Fetch associated languages from project_languages + coding_language_master
                if not proj.get('languages_json') or proj.get('languages_json') == '[]':
                    proj_langs = _pg_fetch_all(conn, '''
                        SELECT clm.language_name
                        FROM project_languages pl
                        JOIN coding_language_master clm ON pl.language_id = clm.language_id
                        WHERE pl.project_id = %s
                    ''', (proj['project_id'],))
                    lang_names = [l['language_name'] for l in proj_langs]
                    if lang_names:
                        proj['languages_json'] = json.dumps(lang_names)
                projects.append(proj)

            # 14. Pitch
            pitch = _pg_fetch_one(conn,
                'SELECT * FROM student_pitch WHERE student_id = %s', (student_id,))

            conn.close()

        else:
            # SQLite fallback (flat schema — language_name stored directly)
            cursor = _sqlite_conn.cursor()

            def _sq(sql, params=()):
                cursor.execute(sql, params)
                return [dict(r) for r in cursor.fetchall()]

            def _sq1(sql, params=()):
                cursor.execute(sql, params)
                r = cursor.fetchone()
                return dict(r) if r else None

            academics_dict = _sq1('SELECT * FROM academic_records WHERE student_id = ?', (student_id,))
            backlogs_list = _sq('SELECT * FROM backlogs WHERE student_id = ?', (student_id,)) if academics_dict else []
            coding_langs = _sq('''
                SELECT cl.student_language_id, cl.student_id, cl.language_id,
                       COALESCE(clm.language_name, 'Language #' || cl.language_id) AS language_name,
                       cl.proficiency_level
                FROM coding_languages cl
                LEFT JOIN coding_language_master clm ON cl.language_id = clm.language_id
                WHERE cl.student_id = ?
            ''', (student_id,))
            tech_skills = _sq('''
                SELECT ts.student_skill_id, ts.student_id, ts.technical_skill_id,
                       COALESCE(tsm.skill_name, 'Skill #' || ts.technical_skill_id) AS skill_name,
                       ts.proficiency_level
                FROM technical_skills ts
                LEFT JOIN technical_skill_master tsm ON ts.technical_skill_id = tsm.technical_skill_id
                WHERE ts.student_id = ?
            ''', (student_id,))
            coding_platforms = _sq('''
                SELECT cp.coding_platform_id, cp.student_id, cp.platform_id,
                       COALESCE(cpm.platform_name, 'Platform #' || cp.platform_id) AS platform_name,
                       cp.profile_url, cp.questions_solved
                FROM coding_platforms cp
                LEFT JOIN coding_platform_master cpm ON cp.platform_id = cpm.platform_id
                WHERE cp.student_id = ?
            ''', (student_id,))
            linkedin = _sq1('SELECT * FROM linkedin_profiles WHERE student_id = ?', (student_id,))
            research_papers = _sq('SELECT * FROM research_papers WHERE student_id = ?', (student_id,))
            for rp in research_papers:
                rp['has_published'] = 1 if rp.get('paper_title') else rp.get('has_published', 0)
            internships = _sq('SELECT * FROM internships WHERE student_id = ?', (student_id,))
            for i in internships:
                i['has_internship'] = 1 if i.get('company_name') else i.get('has_internship', 0)
            hackathons = _sq('SELECT * FROM hackathons WHERE student_id = ?', (student_id,))
            for h in hackathons:
                h['has_hackathon'] = 1 if h.get('hackathon_name') else h.get('has_hackathon', 0)
            certificates = _sq('SELECT * FROM courses_certificates WHERE student_id = ?', (student_id,))
            for c in certificates:
                c['has_certificate'] = 1 if c.get('course_name') else c.get('has_certificate', 0)
            aptitude = _sq('''
                SELECT aps.student_aptitude_id, aps.student_id, aps.aptitude_skill_id,
                       COALESCE(asm.skill_name, 'Aptitude #' || aps.aptitude_skill_id) AS skill_name,
                       aps.proficiency_level
                FROM aptitude_skills aps
                LEFT JOIN aptitude_skill_master asm ON aps.aptitude_skill_id = asm.aptitude_skill_id
                WHERE aps.student_id = ?
            ''', (student_id,))
            communication = _sq('''
                SELECT cs.student_communication_id, cs.student_id, cs.communication_skill_id,
                       COALESCE(csm.skill_name, 'Communication #' || cs.communication_skill_id) AS skill_name,
                       cs.proficiency_level
                FROM communication_skills cs
                LEFT JOIN communication_skill_master csm ON cs.communication_skill_id = csm.communication_skill_id
                WHERE cs.student_id = ?
            ''', (student_id,))
            foreign_langs = _sq('''
                SELECT fl.student_foreign_language_id, fl.student_id, fl.foreign_language_id,
                       COALESCE(flm.language_name, 'Language #' || fl.foreign_language_id) AS language_name,
                       fl.proficiency_level
                FROM foreign_languages fl
                LEFT JOIN foreign_language_master flm ON fl.foreign_language_id = flm.foreign_language_id
                WHERE fl.student_id = ?
            ''', (student_id,))
            projects_raw = _sq('SELECT * FROM projects WHERE student_id = ?', (student_id,))
            projects = []
            for proj in projects_raw:
                proj['has_project'] = 1 if proj.get('project_title') else proj.get('has_project', 0)
                proj_langs = _sq('''
                    SELECT clm.language_name
                    FROM project_languages pl
                    JOIN coding_language_master clm ON pl.language_id = clm.language_id
                    WHERE pl.project_id = ?
                ''', (proj['project_id'],))
                lang_names = [l['language_name'] for l in proj_langs]
                if lang_names:
                    proj['languages_json'] = json.dumps(lang_names)
                projects.append(proj)
            pitch = _sq1('SELECT * FROM student_pitch WHERE student_id = ?', (student_id,))

    except Exception as err:
        print(f"Error fetching card data: {err}")
        if using_pg and conn:
            conn.close()
        academics_dict = None
        backlogs_list = []
        coding_langs = tech_skills = coding_platforms = []
        linkedin = None
        research_papers = internships = hackathons = certificates = []
        aptitude = communication = foreign_langs = projects = []
        pitch = None

    # Determine completion
    student_record = get_student_by_id(student_id)
    current_sem = student_record['current_semester'] if student_record else 1

    # Normalize proficiency_level to string 1-5 for rating circles UI
    for s in tech_skills:
        if s.get('proficiency_level'):
            s['proficiency_level'] = str(PROF_STR_TO_NUM.get(s['proficiency_level'], s['proficiency_level']))
    for a in aptitude:
        if a.get('proficiency_level'):
            a['proficiency_level'] = str(PROF_STR_TO_NUM.get(a['proficiency_level'], a['proficiency_level']))
    for c in communication:
        if c.get('proficiency_level'):
            c['proficiency_level'] = str(PROF_STR_TO_NUM.get(c['proficiency_level'], c['proficiency_level']))

    academics_complete = False
    if academics_dict and academics_dict.get('percentage_10th') is not None and academics_dict.get('percentage_12th') is not None:
        if current_sem > 1:
            sgpa_valid = all(
                academics_dict.get(f'semester_{s}_sgpa') is not None
                for s in range(1, current_sem)
            )
            academics_complete = sgpa_valid
        else:
            academics_complete = True

    # Filter out NONE-named entries for completion check
    valid_coding_langs = [l for l in coding_langs if l.get('language_name', '').upper() != 'NONE']
    valid_tech_skills = [s for s in tech_skills if s.get('skill_name', '').upper() != 'NONE']
    valid_platforms = [p for p in coding_platforms if p.get('platform_name', '').upper() != 'NONE']
    valid_research = [p for p in research_papers if p.get('paper_title')]
    valid_internships = [i for i in internships if i.get('company_name')]
    valid_hackathons = [h for h in hackathons if h.get('hackathon_name')]
    valid_certs = [c for c in certificates if c.get('course_name')]
    valid_projects = [p for p in projects if p.get('project_title')]
    valid_foreign = [f for f in foreign_langs if f.get('language_name', '').upper() != 'NONE']

    completion = {
        'academics': academics_complete,
        'coding_languages': len(coding_langs) > 0,
        'technical_skills': len(tech_skills) > 0,
        'coding_platforms': len(coding_platforms) > 0,
        'linkedin': linkedin is not None,
        'research_papers': len(research_papers) > 0,
        'internships': len(internships) > 0,
        'hackathons': len(hackathons) > 0,
        'courses_certificates': len(certificates) > 0,
        'aptitude': len(aptitude) >= 4,
        'communication': len(communication) >= 4,
        'foreign_languages': len(foreign_langs) > 0,
        'projects': len(projects) > 0,
    }

    cards_completed_count = sum(1 for v in completion.values() if v)

    tech_skills_dict = {s['skill_name']: str(s.get('proficiency_level', '3')) for s in tech_skills if s.get('skill_name')}
    aptitude_dict = {a['skill_name']: str(a.get('proficiency_level', '3')) for a in aptitude if a.get('skill_name')}
    communication_dict = {c['skill_name']: str(c.get('proficiency_level', '3')) for c in communication if c.get('skill_name')}

    if academics_dict:
        sems_marksheets = {}
        if academics_dict.get('marksheet_sems_json'):
            try:
                raw_sm = json.loads(academics_dict['marksheet_sems_json']) if isinstance(academics_dict['marksheet_sems_json'], str) else academics_dict['marksheet_sems_json']
                if isinstance(raw_sm, dict):
                    for k, v in raw_sm.items():
                        sems_marksheets[str(k)] = v
            except Exception:
                sems_marksheets = {}
        academics_dict['sems_marksheets'] = sems_marksheets

    return {
        'academics': academics_dict,
        'backlogs': backlogs_list,
        'coding_languages': coding_langs,
        'technical_skills': tech_skills,
        'technical_skills_dict': tech_skills_dict,
        'coding_platforms': coding_platforms,
        'linkedin': linkedin,
        'research_papers': research_papers,
        'internships': internships,
        'courses_certificates': certificates,
        'hackathons': hackathons,
        'aptitude': aptitude,
        'aptitude_dict': aptitude_dict,
        'communication': communication,
        'communication_dict': communication_dict,
        'foreign_languages': foreign_langs,
        'projects': projects,
        'pitch': pitch,
        'completion': completion,
        'cards_completed_count': cards_completed_count,
        'all_cards_completed': cards_completed_count == 13
    }


# ============================================================
# CARD DATA SAVE — PostgreSQL-aware
# ============================================================

def save_academics_card(student_id, percentage_10th, percentage_12th, sems_sgpa_dict,
                        previous_backlogs, backlogs_list,
                        marksheet_10th_path=None, marksheet_12th_path=None, sems_marksheet_json=None):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO academic_records (
                        student_id, percentage_10th, percentage_12th,
                        semester_1_sgpa, semester_2_sgpa, semester_3_sgpa, semester_4_sgpa,
                        semester_5_sgpa, semester_6_sgpa, semester_7_sgpa, semester_8_sgpa,
                        previous_backlogs, marksheet_10th_path, marksheet_12th_path, marksheet_sems_json, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (student_id) DO UPDATE SET
                        percentage_10th = EXCLUDED.percentage_10th,
                        percentage_12th = EXCLUDED.percentage_12th,
                        semester_1_sgpa = EXCLUDED.semester_1_sgpa,
                        semester_2_sgpa = EXCLUDED.semester_2_sgpa,
                        semester_3_sgpa = EXCLUDED.semester_3_sgpa,
                        semester_4_sgpa = EXCLUDED.semester_4_sgpa,
                        semester_5_sgpa = EXCLUDED.semester_5_sgpa,
                        semester_6_sgpa = EXCLUDED.semester_6_sgpa,
                        semester_7_sgpa = EXCLUDED.semester_7_sgpa,
                        semester_8_sgpa = EXCLUDED.semester_8_sgpa,
                        previous_backlogs = EXCLUDED.previous_backlogs,
                        marksheet_10th_path = COALESCE(EXCLUDED.marksheet_10th_path, academic_records.marksheet_10th_path),
                        marksheet_12th_path = COALESCE(EXCLUDED.marksheet_12th_path, academic_records.marksheet_12th_path),
                        marksheet_sems_json = COALESCE(EXCLUDED.marksheet_sems_json, academic_records.marksheet_sems_json),
                        updated_at = CURRENT_TIMESTAMP
                ''', (
                    student_id, percentage_10th, percentage_12th,
                    sems_sgpa_dict.get(1), sems_sgpa_dict.get(2),
                    sems_sgpa_dict.get(3), sems_sgpa_dict.get(4),
                    sems_sgpa_dict.get(5), sems_sgpa_dict.get(6),
                    sems_sgpa_dict.get(7), sems_sgpa_dict.get(8),
                    previous_backlogs,
                    marksheet_10th_path, marksheet_12th_path, sems_marksheet_json
                ))
                cur.execute('DELETE FROM backlogs WHERE student_id = %s', (student_id,))
                if previous_backlogs and backlogs_list:
                    for b in backlogs_list:
                        if b.get('level') and b.get('subject'):
                            cur.execute(
                                'INSERT INTO backlogs (student_id, academic_level, subject_name) VALUES (%s, %s, %s)',
                                (student_id, b['level'], b['subject'])
                            )
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_academics error: {err}")
            conn.rollback()
            conn.close()

    # SQLite fallback
    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        INSERT INTO academic_records (
            student_id, percentage_10th, percentage_12th,
            semester_1_sgpa, semester_2_sgpa, semester_3_sgpa, semester_4_sgpa,
            semester_5_sgpa, semester_6_sgpa, semester_7_sgpa, semester_8_sgpa,
            previous_backlogs, marksheet_10th_path, marksheet_12th_path, marksheet_sems_json, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_id) DO UPDATE SET
            percentage_10th = excluded.percentage_10th,
            percentage_12th = excluded.percentage_12th,
            semester_1_sgpa = excluded.semester_1_sgpa,
            semester_2_sgpa = excluded.semester_2_sgpa,
            semester_3_sgpa = excluded.semester_3_sgpa,
            semester_4_sgpa = excluded.semester_4_sgpa,
            semester_5_sgpa = excluded.semester_5_sgpa,
            semester_6_sgpa = excluded.semester_6_sgpa,
            semester_7_sgpa = excluded.semester_7_sgpa,
            semester_8_sgpa = excluded.semester_8_sgpa,
            previous_backlogs = excluded.previous_backlogs,
            marksheet_10th_path = COALESCE(excluded.marksheet_10th_path, academic_records.marksheet_10th_path),
            marksheet_12th_path = COALESCE(excluded.marksheet_12th_path, academic_records.marksheet_12th_path),
            marksheet_sems_json = COALESCE(excluded.marksheet_sems_json, academic_records.marksheet_sems_json),
            updated_at = CURRENT_TIMESTAMP
    ''', (
        student_id, percentage_10th, percentage_12th,
        sems_sgpa_dict.get(1), sems_sgpa_dict.get(2), sems_sgpa_dict.get(3), sems_sgpa_dict.get(4),
        sems_sgpa_dict.get(5), sems_sgpa_dict.get(6), sems_sgpa_dict.get(7), sems_sgpa_dict.get(8),
        1 if previous_backlogs else 0, marksheet_10th_path, marksheet_12th_path, sems_marksheet_json
    ))
    cursor.execute('DELETE FROM backlogs WHERE student_id = ?', (student_id,))
    if previous_backlogs and backlogs_list:
        for b in backlogs_list:
            if b.get('level') and b.get('subject'):
                cursor.execute('INSERT INTO backlogs (student_id, academic_level, subject_name) VALUES (?, ?, ?)',
                               (student_id, b['level'], b['subject']))
    _sqlite_conn.commit()


def _pg_get_language_id(cur, language_name):
    """Resolves language_name to language_id in coding_language_master."""
    cur.execute('SELECT language_id FROM coding_language_master WHERE LOWER(language_name) = LOWER(%s)', (language_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    # Insert unknown language
    cur.execute('INSERT INTO coding_language_master (language_name) VALUES (%s) RETURNING language_id', (language_name,))
    return cur.fetchone()[0]


def _sqlite_get_language_id(cursor, language_name):
    """Resolves language_name to language_id in coding_language_master (SQLite)."""
    cursor.execute('SELECT language_id FROM coding_language_master WHERE LOWER(language_name) = LOWER(?)', (language_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO coding_language_master (language_name) VALUES (?)', (language_name,))
    return cursor.lastrowid


def save_coding_languages_card(student_id, langs_list):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM coding_languages WHERE student_id = %s', (student_id,))
                for item in langs_list:
                    lang_name = item.get('language_name', '').strip()
                    prof = item.get('proficiency_level', 'Beginner')
                    if lang_name:
                        lang_id = _pg_get_language_id(cur, lang_name)
                        cur.execute('''
                            INSERT INTO coding_languages (student_id, language_id, proficiency_level)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (student_id, language_id) DO UPDATE SET proficiency_level = EXCLUDED.proficiency_level
                        ''', (student_id, lang_id, prof))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_coding_languages error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM coding_languages WHERE student_id = ?', (student_id,))
    for item in langs_list:
        lang_name = item.get('language_name', '').strip()
        prof = item.get('proficiency_level', 'Beginner')
        if lang_name:
            lang_id = _sqlite_get_language_id(cursor, lang_name)
            cursor.execute(
                'INSERT OR IGNORE INTO coding_languages (student_id, language_id, proficiency_level) VALUES (?, ?, ?)',
                (student_id, lang_id, prof))
    _sqlite_conn.commit()


def _pg_get_technical_skill_id(cur, skill_name):
    """Resolves skill_name to technical_skill_id in technical_skill_master."""
    cur.execute('SELECT technical_skill_id FROM technical_skill_master WHERE LOWER(skill_name) = LOWER(%s)', (skill_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('INSERT INTO technical_skill_master (skill_name) VALUES (%s) RETURNING technical_skill_id', (skill_name,))
    return cur.fetchone()[0]


def _sqlite_get_technical_skill_id(cursor, skill_name):
    """Resolves skill_name to technical_skill_id in technical_skill_master (SQLite)."""
    cursor.execute('SELECT technical_skill_id FROM technical_skill_master WHERE LOWER(skill_name) = LOWER(?)', (skill_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO technical_skill_master (skill_name) VALUES (?)', (skill_name,))
    return cursor.lastrowid


def save_technical_skills_card(student_id, skills_list):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM technical_skills WHERE student_id = %s', (student_id,))
                for item in skills_list:
                    skill_name = item.get('skill_name', '').strip()
                    raw_prof = item.get('proficiency_level', '3')
                    prof = PROF_NUM_TO_STR.get(raw_prof, 'Proficient')
                    if skill_name:
                        skill_id = _pg_get_technical_skill_id(cur, skill_name)
                        cur.execute('''
                            INSERT INTO technical_skills (student_id, technical_skill_id, proficiency_level)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (student_id, technical_skill_id) DO UPDATE SET proficiency_level = EXCLUDED.proficiency_level
                        ''', (student_id, skill_id, prof))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_technical_skills error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM technical_skills WHERE student_id = ?', (student_id,))
    for item in skills_list:
        skill_name = item.get('skill_name', '').strip()
        raw_prof = item.get('proficiency_level', '3')
        prof = PROF_NUM_TO_STR.get(raw_prof, 'Proficient')
        if skill_name:
            skill_id = _sqlite_get_technical_skill_id(cursor, skill_name)
            cursor.execute(
                'INSERT OR IGNORE INTO technical_skills (student_id, technical_skill_id, proficiency_level) VALUES (?, ?, ?)',
                (student_id, skill_id, prof))
    _sqlite_conn.commit()


def _pg_get_platform_id(cur, platform_name):
    """Resolves platform_name to platform_id in coding_platform_master."""
    cur.execute('SELECT platform_id FROM coding_platform_master WHERE LOWER(platform_name) = LOWER(%s)', (platform_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('INSERT INTO coding_platform_master (platform_name) VALUES (%s) RETURNING platform_id', (platform_name,))
    return cur.fetchone()[0]


def _sqlite_get_platform_id(cursor, platform_name):
    """Resolves platform_name to platform_id in coding_platform_master (SQLite)."""
    cursor.execute('SELECT platform_id FROM coding_platform_master WHERE LOWER(platform_name) = LOWER(?)', (platform_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO coding_platform_master (platform_name) VALUES (?)', (platform_name,))
    return cursor.lastrowid


def save_coding_platforms_card(student_id, platforms_list):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM coding_platforms WHERE student_id = %s', (student_id,))
                for item in platforms_list:
                    name = item.get('platform_name', '').strip()
                    if name:
                        plat_id = _pg_get_platform_id(cur, name)
                        cur.execute('''
                            INSERT INTO coding_platforms (student_id, platform_id, profile_url, questions_solved)
                            VALUES (%s, %s, %s, %s)
                        ''', (student_id, plat_id, item.get('profile_url', ''), int(item.get('questions_solved', 0))))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_coding_platforms error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM coding_platforms WHERE student_id = ?', (student_id,))
    for item in platforms_list:
        name = item.get('platform_name', '').strip()
        if name:
            plat_id = _sqlite_get_platform_id(cursor, name)
            cursor.execute(
                'INSERT INTO coding_platforms (student_id, platform_id, profile_url, questions_solved) VALUES (?, ?, ?, ?)',
                (student_id, plat_id, item.get('profile_url', ''), int(item.get('questions_solved', 0))))
    _sqlite_conn.commit()


def save_linkedin_card(student_id, uses_academic, profile_url=None, post_count=0):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO linkedin_profiles (student_id, uses_for_academic_purposes, profile_url, number_of_posts)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (student_id) DO UPDATE SET
                        uses_for_academic_purposes = EXCLUDED.uses_for_academic_purposes,
                        profile_url = EXCLUDED.profile_url,
                        number_of_posts = EXCLUDED.number_of_posts
                ''', (student_id, uses_academic,
                      profile_url if uses_academic else None,
                      int(post_count) if uses_academic else 0))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_linkedin error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        INSERT INTO linkedin_profiles (student_id, uses_for_academic_purposes, profile_url, number_of_posts)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            uses_for_academic_purposes = excluded.uses_for_academic_purposes,
            profile_url = excluded.profile_url,
            number_of_posts = excluded.number_of_posts
    ''', (student_id, 1 if uses_academic else 0, profile_url if uses_academic else '', int(post_count) if uses_academic else 0))
    _sqlite_conn.commit()


def save_research_papers_card(student_id, papers_list, has_published=True):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM research_papers WHERE student_id = %s', (student_id,))
                if not has_published or not papers_list:
                    cur.execute('''
                        INSERT INTO research_papers (student_id, paper_title, has_published)
                        VALUES (%s, %s, 0)
                    ''', (student_id, ''))
                else:
                    for item in papers_list:
                        cur.execute('''
                            INSERT INTO research_papers (student_id, paper_title, publication_name, paper_url, document_path, has_published)
                            VALUES (%s, %s, %s, %s, %s, 1)
                        ''', (student_id,
                              item.get('paper_title', 'Research Paper'),
                              item.get('publication_name', ''),
                              item.get('paper_url', ''),
                              item.get('document_path', '')))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_research_papers error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM research_papers WHERE student_id = ?', (student_id,))
    if not has_published or not papers_list:
        cursor.execute('INSERT INTO research_papers (student_id, has_published, paper_title) VALUES (?, 0, ?)', (student_id, ''))
    else:
        for item in papers_list:
            cursor.execute('''
                INSERT INTO research_papers (student_id, has_published, paper_title, publication_name, paper_url, document_path)
                VALUES (?, 1, ?, ?, ?, ?)
            ''', (student_id, item.get('paper_title', 'Research Paper'), item.get('publication_name', ''), item.get('paper_url', ''), item.get('document_path', '')))
    _sqlite_conn.commit()


def save_internships_card(student_id, internships_list, has_internship=True):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM internships WHERE student_id = %s', (student_id,))
                if not has_internship or not internships_list:
                    cur.execute('''
                        INSERT INTO internships (student_id, company_name, has_internship)
                        VALUES (%s, %s, 0)
                    ''', (student_id, ''))
                else:
                    for item in internships_list:
                        cur.execute('''
                            INSERT INTO internships (student_id, company_name, role, start_date, end_date, offer_letter_path, has_internship)
                            VALUES (%s, %s, %s, %s, %s, %s, 1)
                        ''', (student_id,
                              item.get('company_name', ''),
                              item.get('role', ''),
                              item.get('start_date') or None,
                              item.get('end_date') or None,
                              item.get('offer_letter_path', '')))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_internships error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM internships WHERE student_id = ?', (student_id,))
    if not has_internship or not internships_list:
        cursor.execute('INSERT INTO internships (student_id, has_internship, company_name) VALUES (?, 0, ?)', (student_id, ''))
    else:
        for item in internships_list:
            cursor.execute('''
                INSERT INTO internships (student_id, has_internship, company_name, role, start_date, end_date, offer_letter_path)
                VALUES (?, 1, ?, ?, ?, ?, ?)
            ''', (student_id, item.get('company_name', ''), item.get('role', ''), item.get('start_date', ''), item.get('end_date', ''), item.get('offer_letter_path', '')))
    _sqlite_conn.commit()


def save_hackathons_card(student_id, hackathons_list, has_hackathon=True):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM hackathons WHERE student_id = %s', (student_id,))
                if not has_hackathon or not hackathons_list:
                    cur.execute('''
                        INSERT INTO hackathons (student_id, hackathon_name, has_hackathon)
                        VALUES (%s, %s, 0)
                    ''', (student_id, ''))
                else:
                    for item in hackathons_list:
                        cur.execute('''
                            INSERT INTO hackathons (student_id, hackathon_name, organizer, position, certificate_path, has_hackathon)
                            VALUES (%s, %s, %s, %s, %s, 1)
                        ''', (student_id,
                              item.get('hackathon_name', ''),
                              item.get('organizer', ''),
                              item.get('position', ''),
                              item.get('certificate_path', '')))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_hackathons error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM hackathons WHERE student_id = ?', (student_id,))
    if not has_hackathon or not hackathons_list:
        cursor.execute('INSERT INTO hackathons (student_id, has_hackathon, hackathon_name) VALUES (?, 0, ?)', (student_id, ''))
    else:
        for item in hackathons_list:
            cursor.execute('''
                INSERT INTO hackathons (student_id, has_hackathon, hackathon_name, organizer, position, certificate_path)
                VALUES (?, 1, ?, ?, ?, ?)
            ''', (student_id, item.get('hackathon_name', ''), item.get('organizer', ''), item.get('position', ''), item.get('certificate_path', '')))
    _sqlite_conn.commit()


def save_courses_certificates_card(student_id, certs_list, has_certificate=True):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM courses_certificates WHERE student_id = %s', (student_id,))
                if not has_certificate or not certs_list:
                    cur.execute('''
                        INSERT INTO courses_certificates (student_id, course_name, has_certificate)
                        VALUES (%s, %s, 0)
                    ''', (student_id, ''))
                else:
                    for item in certs_list:
                        cur.execute('''
                            INSERT INTO courses_certificates (student_id, course_name, platform, certificate_path, has_certificate)
                            VALUES (%s, %s, %s, %s, 1)
                        ''', (student_id,
                              item.get('course_name', ''),
                              item.get('platform', ''),
                              item.get('certificate_path', '')))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_courses_certificates error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM courses_certificates WHERE student_id = ?', (student_id,))
    if not has_certificate or not certs_list:
        cursor.execute('INSERT INTO courses_certificates (student_id, has_certificate, course_name) VALUES (?, 0, ?)', (student_id, ''))
    else:
        for item in certs_list:
            cursor.execute('''
                INSERT INTO courses_certificates (student_id, has_certificate, course_name, platform, certificate_path)
                VALUES (?, 1, ?, ?, ?)
            ''', (student_id, item.get('course_name', ''), item.get('platform', ''), item.get('certificate_path', '')))
    _sqlite_conn.commit()


def _pg_get_aptitude_skill_id(cur, skill_name):
    """Resolves skill_name to aptitude_skill_id."""
    cur.execute('SELECT aptitude_skill_id FROM aptitude_skill_master WHERE LOWER(skill_name) = LOWER(%s)', (skill_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('INSERT INTO aptitude_skill_master (skill_name) VALUES (%s) RETURNING aptitude_skill_id', (skill_name,))
    return cur.fetchone()[0]


def _sqlite_get_aptitude_skill_id(cursor, skill_name):
    """Resolves skill_name to aptitude_skill_id in aptitude_skill_master (SQLite)."""
    cursor.execute('SELECT aptitude_skill_id FROM aptitude_skill_master WHERE LOWER(skill_name) = LOWER(?)', (skill_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO aptitude_skill_master (skill_name) VALUES (?)', (skill_name,))
    return cursor.lastrowid


def save_aptitude_card(student_id, skills_list):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM aptitude_skills WHERE student_id = %s', (student_id,))
                for item in skills_list:
                    name = item.get('skill_name', '').strip()
                    raw_prof = item.get('proficiency_level', '3')
                    prof = PROF_NUM_TO_STR.get(raw_prof, 'Proficient')
                    if name:
                        skill_id = _pg_get_aptitude_skill_id(cur, name)
                        cur.execute('''
                            INSERT INTO aptitude_skills (student_id, aptitude_skill_id, proficiency_level)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (student_id, aptitude_skill_id) DO UPDATE SET proficiency_level = EXCLUDED.proficiency_level
                        ''', (student_id, skill_id, prof))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_aptitude error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM aptitude_skills WHERE student_id = ?', (student_id,))
    for item in skills_list:
        name = item.get('skill_name', '').strip()
        raw_prof = item.get('proficiency_level', '3')
        prof = PROF_NUM_TO_STR.get(raw_prof, 'Proficient')
        if name:
            skill_id = _sqlite_get_aptitude_skill_id(cursor, name)
            cursor.execute(
                'INSERT OR IGNORE INTO aptitude_skills (student_id, aptitude_skill_id, proficiency_level) VALUES (?, ?, ?)',
                (student_id, skill_id, prof))
    _sqlite_conn.commit()


def _pg_get_communication_skill_id(cur, skill_name):
    """Resolves skill_name to communication_skill_id."""
    cur.execute('SELECT communication_skill_id FROM communication_skill_master WHERE LOWER(skill_name) = LOWER(%s)', (skill_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('INSERT INTO communication_skill_master (skill_name) VALUES (%s) RETURNING communication_skill_id', (skill_name,))
    return cur.fetchone()[0]


def _sqlite_get_communication_skill_id(cursor, skill_name):
    """Resolves skill_name to communication_skill_id in communication_skill_master (SQLite)."""
    cursor.execute('SELECT communication_skill_id FROM communication_skill_master WHERE LOWER(skill_name) = LOWER(?)', (skill_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO communication_skill_master (skill_name) VALUES (?)', (skill_name,))
    return cursor.lastrowid


def save_communication_card(student_id, skills_list):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM communication_skills WHERE student_id = %s', (student_id,))
                for item in skills_list:
                    name = item.get('skill_name', '').strip()
                    raw_prof = item.get('proficiency_level', '3')
                    prof = PROF_NUM_TO_STR.get(raw_prof, 'Proficient')
                    if name:
                        skill_id = _pg_get_communication_skill_id(cur, name)
                        cur.execute('''
                            INSERT INTO communication_skills (student_id, communication_skill_id, proficiency_level)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (student_id, communication_skill_id) DO UPDATE SET proficiency_level = EXCLUDED.proficiency_level
                        ''', (student_id, skill_id, prof))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_communication error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM communication_skills WHERE student_id = ?', (student_id,))
    for item in skills_list:
        name = item.get('skill_name', '').strip()
        raw_prof = item.get('proficiency_level', '3')
        prof = PROF_NUM_TO_STR.get(raw_prof, 'Proficient')
        if name:
            skill_id = _sqlite_get_communication_skill_id(cursor, name)
            cursor.execute(
                'INSERT OR IGNORE INTO communication_skills (student_id, communication_skill_id, proficiency_level) VALUES (?, ?, ?)',
                (student_id, skill_id, prof))
    _sqlite_conn.commit()


def _pg_get_foreign_language_id(cur, language_name):
    """Resolves language_name to foreign_language_id."""
    cur.execute('SELECT foreign_language_id FROM foreign_language_master WHERE LOWER(language_name) = LOWER(%s)', (language_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute('INSERT INTO foreign_language_master (language_name) VALUES (%s) RETURNING foreign_language_id', (language_name,))
    return cur.fetchone()[0]


def _sqlite_get_foreign_language_id(cursor, language_name):
    """Resolves language_name to foreign_language_id in foreign_language_master (SQLite)."""
    cursor.execute('SELECT foreign_language_id FROM foreign_language_master WHERE LOWER(language_name) = LOWER(?)', (language_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute('INSERT INTO foreign_language_master (language_name) VALUES (?)', (language_name,))
    return cursor.lastrowid


def save_foreign_languages_card(student_id, langs_list):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM foreign_languages WHERE student_id = %s', (student_id,))
                for item in langs_list:
                    name = item.get('language_name', '').strip()
                    prof = item.get('proficiency_level', 'Beginner')
                    if name:
                        lang_id = _pg_get_foreign_language_id(cur, name)
                        cur.execute('''
                            INSERT INTO foreign_languages (student_id, foreign_language_id, proficiency_level)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (student_id, foreign_language_id) DO UPDATE SET proficiency_level = EXCLUDED.proficiency_level
                        ''', (student_id, lang_id, prof))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_foreign_languages error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM foreign_languages WHERE student_id = ?', (student_id,))
    for item in langs_list:
        name = item.get('language_name', '').strip()
        prof = item.get('proficiency_level', 'Beginner')
        if name:
            lang_id = _sqlite_get_foreign_language_id(cursor, name)
            cursor.execute(
                'INSERT OR IGNORE INTO foreign_languages (student_id, foreign_language_id, proficiency_level) VALUES (?, ?, ?)',
                (student_id, lang_id, prof))
    _sqlite_conn.commit()


def save_projects_card(student_id, projects_list, has_project=True):
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Delete existing project_languages and projects
                cur.execute('''
                    DELETE FROM project_languages WHERE project_id IN (
                        SELECT project_id FROM projects WHERE student_id = %s
                    )
                ''', (student_id,))
                cur.execute('DELETE FROM projects WHERE student_id = %s', (student_id,))
                if not has_project or not projects_list:
                    cur.execute('''
                        INSERT INTO projects (student_id, project_title, has_project)
                        VALUES (%s, %s, 0)
                    ''', (student_id, ''))
                else:
                    for item in projects_list:
                        title = item.get('project_title', '').strip()
                        if title:
                            cur.execute('''
                                INSERT INTO projects (student_id, project_title, github_url, project_description, has_project)
                                VALUES (%s, %s, %s, %s, 1)
                                RETURNING project_id
                            ''', (student_id, title, item.get('github_url', ''), item.get('project_description', '')))
                            project_id = cur.fetchone()[0]
                            # Insert project languages
                            try:
                                lang_names = json.loads(item.get('languages_json', '[]') or '[]')
                            except Exception:
                                lang_names = []
                            for lang_name in lang_names:
                                if lang_name and str(lang_name).strip():
                                    lang_id = _pg_get_language_id(cur, str(lang_name).strip())
                                    cur.execute('''
                                        INSERT INTO project_languages (project_id, language_id)
                                        VALUES (%s, %s)
                                        ON CONFLICT (project_id, language_id) DO NOTHING
                                    ''', (project_id, lang_id))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_projects error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('DELETE FROM projects WHERE student_id = ?', (student_id,))
    if not has_project or not projects_list:
        cursor.execute('INSERT INTO projects (student_id, has_project, project_title) VALUES (?, 0, ?)', (student_id, ''))
    else:
        for item in projects_list:
            cursor.execute('''
                INSERT INTO projects (student_id, has_project, project_title, github_url, project_description, languages_json)
                VALUES (?, 1, ?, ?, ?, ?)
            ''', (student_id, item.get('project_title', ''), item.get('github_url', ''), item.get('project_description', ''), item.get('languages_json', '[]')))
    _sqlite_conn.commit()


def save_pitch_card(student_id, answer):
    conn = get_connection()
    words = len(answer.strip().split()) if answer else 0
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO student_pitch (student_id, answer, word_count, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (student_id) DO UPDATE SET
                        answer = EXCLUDED.answer,
                        word_count = EXCLUDED.word_count,
                        updated_at = CURRENT_TIMESTAMP
                ''', (student_id, answer, words))
            conn.commit()
            conn.close()
            return
        except Exception as err:
            print(f"PG save_pitch error: {err}")
            conn.rollback()
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        INSERT INTO student_pitch (student_id, answer, word_count, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(student_id) DO UPDATE SET
            answer = excluded.answer,
            word_count = excluded.word_count,
            updated_at = CURRENT_TIMESTAMP
    ''', (student_id, answer, words))
    _sqlite_conn.commit()


# ============================================================
# ASSESSMENTS — PostgreSQL-aware
# ============================================================

def record_assessment_run(student_id, total_score, classification, category_scores, skill_gaps, recommendations):
    """Records an assessment calculation run and category scores into the database."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO assessments (student_id, total_score, classification)
                    VALUES (%s, %s, %s)
                    RETURNING assessment_id
                ''', (student_id, total_score, classification))
                assessment_id = cur.fetchone()[0]

                for cs in category_scores:
                    cur.execute('''
                        INSERT INTO assessment_category_scores (assessment_id, category_name, category_score, maximum_score, weightage)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (assessment_id, category_name) DO UPDATE SET
                            category_score = EXCLUDED.category_score
                    ''', (assessment_id, cs['category_name'], cs['category_score'], cs['maximum_score'], cs['weightage']))

                for sg in skill_gaps:
                    sg_prio = 'Mid' if str(sg.get('priority', '')).lower() == 'medium' else sg.get('priority')
                    cur.execute('''
                        INSERT INTO skill_gaps (assessment_id, category_name, current_value, target_value, gap_description, priority)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (assessment_id, sg['category_name'], sg['current_value'], sg['target_value'], sg['gap_description'], sg_prio))

                for rec in recommendations:
                    rec_prio = 'Mid' if str(rec.get('priority', '')).lower() == 'medium' else rec.get('priority')
                    cur.execute('''
                        INSERT INTO recommendations (assessment_id, category_name, recommendation, priority)
                        VALUES (%s, %s, %s, %s)
                    ''', (assessment_id, rec['category_name'], rec['recommendation'], rec_prio))

            conn.commit()
            conn.close()
            return assessment_id
        except Exception as err:
            print(f"PG record_assessment error: {err}")
            conn.rollback()
            conn.close()

    # SQLite fallback
    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        INSERT INTO assessments (student_id, total_score, classification)
        VALUES (?, ?, ?)
    ''', (student_id, total_score, classification))
    assessment_id = cursor.lastrowid

    for cs in category_scores:
        cursor.execute('''
            INSERT INTO assessment_category_scores (assessment_id, category_name, category_score, maximum_score, weightage)
            VALUES (?, ?, ?, ?, ?)
        ''', (assessment_id, cs['category_name'], cs['category_score'], cs['maximum_score'], cs['weightage']))

    for sg in skill_gaps:
        sg_prio = 'Mid' if str(sg.get('priority', '')).lower() == 'medium' else sg.get('priority')
        cursor.execute('''
            INSERT INTO skill_gaps (assessment_id, category_name, current_value, target_value, gap_description, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (assessment_id, sg['category_name'], sg['current_value'], sg['target_value'], sg['gap_description'], sg_prio))

    for rec in recommendations:
        rec_prio = 'Mid' if str(rec.get('priority', '')).lower() == 'medium' else rec.get('priority')
        cursor.execute('''
            INSERT INTO recommendations (assessment_id, category_name, recommendation, priority)
            VALUES (?, ?, ?, ?)
        ''', (assessment_id, rec['category_name'], rec['recommendation'], rec_prio))

    _sqlite_conn.commit()
    return assessment_id


def get_assessment_history(student_id):
    """Retrieves all past assessment runs for a student for progress tracking."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT assessment_id, assessment_date, total_score, classification
                    FROM assessments
                    WHERE student_id = %s
                    ORDER BY assessment_date ASC
                ''', (student_id,))
                rows = [dict(r) for r in cur.fetchall()]
                conn.close()
                return rows
        except Exception as err:
            print(f"PG get_assessment_history error: {err}")
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        SELECT assessment_id, assessment_date, total_score, classification
        FROM assessments WHERE student_id = ?
        ORDER BY assessment_date ASC
    ''', (student_id,))
    return [dict(r) for r in cursor.fetchall()]


def get_latest_assessment(student_id):
    """Retrieves the latest assessment run and breakdown details for a student."""
    conn = get_connection()
    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT assessment_id, assessment_date, total_score, classification
                    FROM assessments
                    WHERE student_id = %s
                    ORDER BY assessment_id DESC LIMIT 1
                ''', (student_id,))
                assessment = cur.fetchone()
                if not assessment:
                    conn.close()
                    return None
                ass_dict = dict(assessment)
                aid = ass_dict['assessment_id']

                cur.execute('SELECT category_name, category_score, maximum_score, weightage FROM assessment_category_scores WHERE assessment_id = %s', (aid,))
                raw_scores = [dict(r) for r in cur.fetchall()]
                clean_scores = []
                for cs in raw_scores:
                    cname = cs['category_name'].lower()
                    if 'hire' in cname or 'pitch' in cname:
                        continue
                    if cs['category_name'] == 'Projects':
                        cs['maximum_score'] = 20.0
                        cs['weightage'] = 20.0
                    clean_scores.append(cs)
                ass_dict['category_scores'] = clean_scores

                cur.execute('SELECT category_name, current_value, target_value, gap_description, priority FROM skill_gaps WHERE assessment_id = %s', (aid,))
                ass_dict['skill_gaps'] = [dict(r) for r in cur.fetchall() if 'hire' not in r['category_name'].lower() and 'pitch' not in r['category_name'].lower()]

                cur.execute('SELECT category_name, recommendation, priority FROM recommendations WHERE assessment_id = %s', (aid,))
                ass_dict['recommendations'] = [dict(r) for r in cur.fetchall() if 'hire' not in r['category_name'].lower() and 'pitch' not in r['category_name'].lower()]

                prio_order = {'High': 1, 'high': 1, 'HIGH': 1, 'Mid': 2, 'mid': 2, 'MID': 2, 'Medium': 2, 'medium': 2, 'MEDIUM': 2, 'Low': 3, 'low': 3, 'LOW': 3}
                for sg in ass_dict['skill_gaps']:
                    if sg.get('priority', '').lower() == 'medium':
                        sg['priority'] = 'Mid'
                for rec in ass_dict['recommendations']:
                    if rec.get('priority', '').lower() == 'medium':
                        rec['priority'] = 'Mid'
                ass_dict['skill_gaps'].sort(key=lambda x: prio_order.get(x.get('priority'), 99))
                ass_dict['recommendations'].sort(key=lambda x: prio_order.get(x.get('priority'), 99))

                conn.close()
                return ass_dict
        except Exception as err:
            print(f"PG get_latest_assessment error: {err}")
            conn.close()

    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        SELECT assessment_id, assessment_date, total_score, classification
        FROM assessments WHERE student_id = ?
        ORDER BY assessment_id DESC LIMIT 1
    ''', (student_id,))
    assessment = cursor.fetchone()
    if not assessment:
        return None
    ass_dict = dict(assessment)
    aid = ass_dict['assessment_id']

    cursor.execute('SELECT category_name, category_score, maximum_score, weightage FROM assessment_category_scores WHERE assessment_id = ?', (aid,))
    raw_scores = [dict(r) for r in cursor.fetchall()]
    clean_scores = []
    for cs in raw_scores:
        cname = cs['category_name'].lower()
        if 'hire' in cname or 'pitch' in cname:
            continue
        if cs['category_name'] == 'Projects':
            cs['maximum_score'] = 20.0
            cs['weightage'] = 20.0
        clean_scores.append(cs)
    ass_dict['category_scores'] = clean_scores

    cursor.execute('SELECT category_name, current_value, target_value, gap_description, priority FROM skill_gaps WHERE assessment_id = ?', (aid,))
    ass_dict['skill_gaps'] = [dict(r) for r in cursor.fetchall() if 'hire' not in r['category_name'].lower() and 'pitch' not in r['category_name'].lower()]

    cursor.execute('SELECT category_name, recommendation, priority FROM recommendations WHERE assessment_id = ?', (aid,))
    ass_dict['recommendations'] = [dict(r) for r in cursor.fetchall() if 'hire' not in r['category_name'].lower() and 'pitch' not in r['category_name'].lower()]

    prio_order = {'High': 1, 'high': 1, 'HIGH': 1, 'Mid': 2, 'mid': 2, 'MID': 2, 'Medium': 2, 'medium': 2, 'MEDIUM': 2, 'Low': 3, 'low': 3, 'LOW': 3}
    for sg in ass_dict['skill_gaps']:
        if sg.get('priority', '').lower() == 'medium':
            sg['priority'] = 'Mid'
    for rec in ass_dict['recommendations']:
        if rec.get('priority', '').lower() == 'medium':
            rec['priority'] = 'Mid'
    ass_dict['skill_gaps'].sort(key=lambda x: prio_order.get(x.get('priority'), 99))
    ass_dict['recommendations'].sort(key=lambda x: prio_order.get(x.get('priority'), 99))

    return ass_dict


# ============================================================
# ADMIN VIEWS — PostgreSQL-aware
# ============================================================

def get_all_students_for_admin():
    """Retrieves list of all students with latest score and breakdown for Admin view."""
    conn = get_connection()

    if conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute('''
                    SELECT s.student_id, s.prn, s.full_name, s.email, s.college,
                           s.current_year, s.current_semester, s.graduation_year,
                           d.department_name,
                           a.total_score, a.classification, a.assessment_date,
                           ar.percentage_10th, ar.percentage_12th, ar.previous_backlogs
                    FROM students s
                    JOIN departments d ON s.department_id = d.department_id
                    LEFT JOIN LATERAL (
                        SELECT total_score, classification, assessment_date
                        FROM assessments
                        WHERE student_id = s.student_id
                        ORDER BY assessment_id DESC LIMIT 1
                    ) a ON TRUE
                    LEFT JOIN academic_records ar ON s.student_id = ar.student_id
                    ORDER BY s.student_id ASC
                ''')
                rows = [dict(r) for r in cur.fetchall()]

                result = []
                for item in rows:
                    sid = item['student_id']

                    # Average SGPA
                    cur.execute('''
                        SELECT semester_1_sgpa, semester_2_sgpa, semester_3_sgpa, semester_4_sgpa,
                               semester_5_sgpa, semester_6_sgpa, semester_7_sgpa, semester_8_sgpa
                        FROM academic_records WHERE student_id = %s
                    ''', (sid,))
                    acad = cur.fetchone()
                    sgpas = []
                    if acad:
                        for k in ['semester_1_sgpa', 'semester_2_sgpa', 'semester_3_sgpa',
                                  'semester_4_sgpa', 'semester_5_sgpa', 'semester_6_sgpa',
                                  'semester_7_sgpa', 'semester_8_sgpa']:
                            if acad[k] is not None:
                                sgpas.append(float(acad[k]))
                    item['avg_sgpa'] = round(sum(sgpas) / len(sgpas), 2) if sgpas else 0.0

                    # Backlogs count
                    cur.execute('SELECT COUNT(*) as cnt FROM backlogs WHERE student_id = %s', (sid,))
                    b_row = cur.fetchone()
                    item['backlogs_count'] = b_row['cnt'] if b_row else 0

                    # Null-safe score defaults
                    item.setdefault('total_score', 0.0)
                    item.setdefault('classification', 'Needs Improvement')
                    if item['total_score'] is None:
                        item['total_score'] = 0.0

                    # Category score breakdown from latest assessment
                    cur.execute('''
                        SELECT category_name, category_score
                        FROM assessment_category_scores
                        WHERE assessment_id = (
                            SELECT assessment_id FROM assessments
                            WHERE student_id = %s
                            ORDER BY assessment_id DESC LIMIT 1
                        )
                    ''', (sid,))
                    cs_rows = cur.fetchall()
                    for cs in cs_rows:
                        cname = cs['category_name'].lower()
                        if 'acad' in cname:
                            item['acad_score'] = float(cs['category_score'])
                        elif 'lang' in cname and 'foreign' not in cname:
                            item['lang_score'] = float(cs['category_score'])
                        elif 'tech' in cname:
                            item['tech_score'] = float(cs['category_score'])
                        elif 'plat' in cname:
                            item['plat_score'] = float(cs['category_score'])
                        elif 'link' in cname:
                            item['link_score'] = float(cs['category_score'])
                        elif 'res' in cname:
                            item['res_score'] = float(cs['category_score'])
                        elif 'intern' in cname:
                            item['int_score'] = float(cs['category_score'])
                        elif 'hack' in cname:
                            item['hack_score'] = float(cs['category_score'])
                        elif 'cert' in cname:
                            item['cert_score'] = float(cs['category_score'])
                        elif 'apt' in cname:
                            item['apt_score'] = float(cs['category_score'])
                        elif 'comm' in cname:
                            item['comm_score'] = float(cs['category_score'])
                        elif 'foreign' in cname:
                            item['for_score'] = float(cs['category_score'])
                        elif 'proj' in cname:
                            item['proj_score'] = float(cs['category_score'])

                    result.append(item)

                conn.close()
                return result

        except Exception as err:
            print(f"PG get_all_students_for_admin error: {err}")
            conn.close()

    # SQLite fallback (no sample seeding — only real SQLite data)
    cursor = _sqlite_conn.cursor()
    cursor.execute('''
        SELECT s.student_id, s.prn, s.full_name, s.email, s.college, s.current_year, s.current_semester, s.graduation_year,
               d.department_name,
               a.total_score, a.classification, a.assessment_date,
               ar.percentage_10th, ar.percentage_12th, ar.previous_backlogs
        FROM students s
        JOIN departments d ON s.department_id = d.department_id
        LEFT JOIN (
            SELECT student_id, total_score, classification, assessment_date,
                   ROW_NUMBER() OVER(PARTITION BY student_id ORDER BY assessment_id DESC) as rn
            FROM assessments
        ) a ON s.student_id = a.student_id AND a.rn = 1
        LEFT JOIN academic_records ar ON s.student_id = ar.student_id
        ORDER BY s.student_id ASC
    ''')
    rows = cursor.fetchall()
    result = []
    for r in rows:
        item = dict(r)
        sid = item['student_id']

        cursor.execute('SELECT semester_1_sgpa, semester_2_sgpa, semester_3_sgpa, semester_4_sgpa, semester_5_sgpa, semester_6_sgpa, semester_7_sgpa, semester_8_sgpa FROM academic_records WHERE student_id = ?', (sid,))
        acad = cursor.fetchone()
        sgpas = []
        if acad:
            for k in acad.keys():
                if k.endswith('_sgpa') and acad[k] is not None:
                    sgpas.append(float(acad[k]))
        item['avg_sgpa'] = round(sum(sgpas) / len(sgpas), 2) if sgpas else 0.0

        cursor.execute('SELECT COUNT(*) as cnt FROM backlogs WHERE student_id = ?', (sid,))
        b_row = cursor.fetchone()
        item['backlogs_count'] = b_row['cnt'] if b_row else 0

        item.setdefault('total_score', 0.0)
        item.setdefault('classification', 'Needs Improvement')
        if item['total_score'] is None:
            item['total_score'] = 0.0

        cursor.execute('SELECT category_name, category_score FROM assessment_category_scores WHERE assessment_id = (SELECT assessment_id FROM assessments WHERE student_id = ? ORDER BY assessment_id DESC LIMIT 1)', (sid,))
        cs_rows = cursor.fetchall()
        for cs in cs_rows:
            cname = cs['category_name'].lower()
            if 'acad' in cname: item['acad_score'] = cs['category_score']
            elif 'lang' in cname and 'foreign' not in cname: item['lang_score'] = cs['category_score']
            elif 'tech' in cname: item['tech_score'] = cs['category_score']
            elif 'plat' in cname: item['plat_score'] = cs['category_score']
            elif 'link' in cname: item['link_score'] = cs['category_score']
            elif 'res' in cname: item['res_score'] = cs['category_score']
            elif 'intern' in cname: item['int_score'] = cs['category_score']
            elif 'hack' in cname: item['hack_score'] = cs['category_score']
            elif 'cert' in cname: item['cert_score'] = cs['category_score']
            elif 'apt' in cname: item['apt_score'] = cs['category_score']
            elif 'comm' in cname: item['comm_score'] = cs['category_score']
            elif 'foreign' in cname: item['for_score'] = cs['category_score']
            elif 'proj' in cname: item['proj_score'] = cs['category_score']

        result.append(item)

    return result


def get_full_student_profile_admin(student_id):
    """Retrieves complete profile, 13 cards data, and assessment history for Admin inspection."""
    student_info = get_student_by_id(student_id)
    if not student_info:
        return None

    card_data = get_student_card_data(student_id)
    latest_assessment = get_latest_assessment(student_id)
    history = get_assessment_history(student_id)

    return {
        'student': student_info,
        'card_data': card_data,
        'latest_assessment': latest_assessment,
        'assessment_history': history
    }


def seed_sample_students_if_empty():
    """Seeds database from app.sql if students table is empty."""
    seed_from_app_sql()
