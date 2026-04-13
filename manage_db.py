import os
import argparse
from pathlib import Path
from mutagen.easyid3 import EasyID3
import mutagen
import database

def reset_database(db_path):
    print(f"\n=== Resetting Database ===")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"  [+] Database at {db_path} has been permanently deleted.")
        except Exception as e:
            print(f"  [X] Could not delete database: {e}")
            return
    else:
        print(f"  [!] No database found at {db_path}.")
        
    print("  [~] Initializing fresh database...")
    database.init_db(db_path)
    print("  [+] Database reset complete.")

def scan_directory(target_dir, db_path):
    print(f"\n=== Scanning Directory to populate Database ===")
    target_path = Path(target_dir)
    if not target_path.exists() or not target_path.is_dir():
        print(f"  [X] Error: Directory '{target_dir}' does not exist.")
        return
        
    print(f"  [~] Ensuring target database exists...")
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    
    supported_extensions = ("*.mp3", "*.m4a", "*.flac", "*.wav", "*.wma", "*.aac")
    audio_files = []
    for ext in supported_extensions:
        audio_files.extend(list(target_path.rglob(ext)))
        audio_files.extend(list(target_path.rglob(ext.upper())))
        
    if not audio_files:
        print("  [!] No supported audio files found.")
        return
        
    success_count = 0
    print(f"  [~] Scanning {len(audio_files)} files to populate the database...")
    
    for file in audio_files:
        if file.name.startswith('.'):
            continue
            
        try:
            # Physical file extraction
            duration = None
            bitrate = None
            file_mut = mutagen.File(file)
            if file_mut and file_mut.info:
                duration = int(file_mut.info.length) if hasattr(file_mut.info, 'length') else None
                bitrate = int(file_mut.info.bitrate / 1000) if hasattr(file_mut.info, 'bitrate') else None

            # ID3 extraction
            audio_tags = EasyID3(file)
            title = audio_tags.get('title', [None])[0]
            artist = audio_tags.get('artist', [None])[0]
            album = audio_tags.get('album', [None])[0]
            genre = audio_tags.get('genre', [None])[0]
            raw_year = audio_tags.get('date', [None])[0]
            track_number = audio_tags.get('tracknumber', [None])[0]
            
            release_year = None
            if raw_year and len(str(raw_year)) >= 4:
                release_year = int(str(raw_year)[:4])
            
            # Fallback to folder structure if tags are missing
            if not artist or not album:
                try:
                    rel_path = file.relative_to(target_path)
                    parts = rel_path.parts
                    if len(parts) >= 3 and not artist:
                        artist = parts[-3]
                    if len(parts) >= 2 and not album:
                        album = parts[-2]
                except ValueError:
                    pass
                    
            title = title if title else file.stem
            artist = artist if artist else "Unknown Artist"
            album = album if album else "Unknown Album"
            
            # Paths in DB are relative to the target_dir (which is usually the organized library)
            relative_path = os.path.relpath(file, target_dir)
            relative_path = Path(relative_path).as_posix()
            
            art_id = database.get_or_create_artist(conn, artist)
            rec_id = database.get_or_create_record(conn, art_id, album, release_year=release_year, genre=genre)
            database.insert_song(
                conn, rec_id, title, relative_path,
                duration=duration, bitrate=bitrate, track_number=track_number
            )
            
            # Mark as processed in cache too so the organizer will naturally skip these files
            database.mark_file_processed(conn, str(file), os.path.getsize(file))
            
            success_count += 1
        except Exception as e:
            # We fail silently instead of throwing errors on every mangled item.
            pass
            
    conn.close()
    print(f"  [+] Scan complete. Successfully indexed {success_count}/{len(audio_files)} tracks into the database.")

def main():
    parser = argparse.ArgumentParser(description="Database Management Toolkit")
    parser.add_argument("--db", required=True, help="Path to the database file")
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the database")
    parser.add_argument("--scan", help="Recursively scan an organized directory and inject into the DB")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database(args.db)
        
    if args.scan:
        scan_directory(args.scan, args.db)

if __name__ == "__main__":
    main()
