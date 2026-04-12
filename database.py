import sqlite3
import json
from pathlib import Path

def get_connection(db_path):
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path):
    """Initializes the database schema if it doesn't exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Create Artists Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # Create Records/Albums Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        release_year INTEGER,
        FOREIGN KEY (artist_id) REFERENCES artists (id),
        UNIQUE(artist_id, title)
    )
    ''')
    
    # Create Songs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        track_file_path TEXT NOT NULL UNIQUE,
        FOREIGN KEY (record_id) REFERENCES records (id)
    )
    ''')
    
    # Create Processed Sources Table (Cache)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_path TEXT NOT NULL,
        byte_size INTEGER NOT NULL,
        UNIQUE(source_path, byte_size)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_or_create_artist(conn, name):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM artists WHERE name = ?', (name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    else:
        cursor.execute('INSERT INTO artists (name) VALUES (?)', (name,))
        conn.commit()
        return cursor.lastrowid

def get_or_create_record(conn, artist_id, title, release_year=None):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM records WHERE artist_id = ? AND title = ?', (artist_id, title))
    row = cursor.fetchone()
    if row:
        return row['id']
    else:
        cursor.execute('INSERT INTO records (artist_id, title, release_year) VALUES (?, ?, ?)', (artist_id, title, release_year))
        conn.commit()
        return cursor.lastrowid

def insert_song(conn, record_id, title, relative_path):
    cursor = conn.cursor()
    # Check if song path already exists to avoid duplicates
    cursor.execute('SELECT id FROM songs WHERE track_file_path = ?', (relative_path,))
    row = cursor.fetchone()
    if row:
        return row['id']
    
    cursor.execute('INSERT INTO songs (record_id, title, track_file_path) VALUES (?, ?, ?)', (record_id, title, relative_path))
    conn.commit()
    return cursor.lastrowid

def is_file_processed(conn, source_path, byte_size):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM processed_sources WHERE source_path = ? AND byte_size = ?', (source_path, byte_size))
    return cursor.fetchone() is not None

def mark_file_processed(conn, source_path, byte_size):
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO processed_sources (source_path, byte_size) VALUES (?, ?)', (source_path, byte_size))
    conn.commit()
