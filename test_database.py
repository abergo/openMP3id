import os
import unittest
from pathlib import Path
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_openmp3id.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        database.init_db(self.db_path)
        self.conn = database.get_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_schema_and_inserts(self):
        # Insert Artist ensuring deduplication works
        art_id = database.get_or_create_artist(self.conn, "Test Artist")
        self.assertIsNotNone(art_id)
        
        # Second call to same artist should return the exact same ID
        art_id2 = database.get_or_create_artist(self.conn, "Test Artist")
        self.assertEqual(art_id, art_id2)
        
        # Insert Record ensuring relation schema works
        rec_id = database.get_or_create_record(self.conn, art_id, "Test Album", 2024)
        self.assertIsNotNone(rec_id)
        
        rec_id2 = database.get_or_create_record(self.conn, art_id, "Test Album", 2024)
        self.assertEqual(rec_id, rec_id2)
        
        # Insert Song mapped to relative path
        song_id = database.insert_song(self.conn, rec_id, "Test Track", "Test Artist/Test Album/Test Track.mp3")
        self.assertIsNotNone(song_id)

        # Insert Duplicate song path shouldn't crash SQLite, should return same ID handled gracefully
        song_id2 = database.insert_song(self.conn, rec_id, "Test Track", "Test Artist/Test Album/Test Track.mp3")
        self.assertEqual(song_id, song_id2)

if __name__ == "__main__":
    unittest.main()
