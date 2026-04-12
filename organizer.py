import os
import shutil
import asyncio
import argparse
from pathlib import Path
import re
import tempfile
from pydub import AudioSegment
import aiohttp
from shazamio import Shazam
from mutagen.easyid3 import EasyID3
import mutagen
from mutagen.id3 import ID3NoHeaderError, ID3, APIC, USLT
import database

def sanitize_filename(name):
    # Remove characters that are problematic in filenames on Windows/Linux/Mac
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

async def download_image(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"      [~] Warning: Failed to download cover art: {e}")
    return None

async def process_file(shazam, input_file, output_dir, conn, original_file_path=None, base_input_dir=None):
    if original_file_path is None:
        original_file_path = input_file
        
    print(f"Processing: {original_file_path.name}")
    try:
        # identify the song
        out = await shazam.recognize(str(input_file))
        
        cover_art_url = None
        lyrics_text = ""
        
        if 'track' not in out:
            print(f"  [!] Shazam could not recognize {original_file_path.name}. Initiating fallback...")
            
            title, artist, album = None, None, None
            
            # Fallback 1: Try existing ID3 tags
            try:
                audio_tags = EasyID3(input_file)
                title = audio_tags.get('title', [None])[0]
                artist = audio_tags.get('artist', [None])[0]
                album = audio_tags.get('album', [None])[0]
            except Exception:
                pass
                
            # Fallback 2: Extract from folder structure
            if not artist or not album:
                if base_input_dir:
                    try:
                        rel_path = original_file_path.relative_to(base_input_dir)
                        parts = rel_path.parts
                        
                        # Expected structure: Artist / Album / Track.ext
                        if len(parts) >= 3 and not artist:
                            artist = parts[-3]
                        if len(parts) >= 2 and not album:
                            album = parts[-2]
                    except ValueError:
                        pass
                        
            # If all fallbacks fail, move bare file to unknown
            if not artist or not title:
                print(f"  [X] Full metadata failure. Moving to Unknown.")
                unknown_dir = output_dir / "Unknown"
                unknown_dir.mkdir(parents=True, exist_ok=True)
                target_path = unknown_dir / original_file_path.with_suffix('.mp3').name
                shutil.copy2(input_file, target_path)
                
                # Register in cache even if unknown so we don't repeatedly fail on it
                try:
                    database.mark_file_processed(conn, str(original_file_path), os.path.getsize(original_file_path))
                except Exception:
                    pass
                return
            else:
                title = title if title else original_file_path.stem
                album = album if album else "Unknown Album"
                print(f"  [>] Recovered Metadata: Artist='{artist}', Album='{album}'")
        else:
            track = out['track']
            title = track.get('title', 'Unknown Title')
            artist = track.get('subtitle', 'Unknown Artist')
            
            # Extract Album, Cover Art, and Lyrics if available
            album = "Unknown Album"
            cover_art_url = track.get('images', {}).get('coverart')
            
            if 'sections' in track:
                for section in track['sections']:
                    if section.get('type') == 'SONG':
                        for meta in section.get('metadata', []):
                            if meta.get('title') == 'Album':
                                album = meta.get('text')
                                break
                    elif section.get('type') == 'LYRICS':
                        lyrics = section.get('text', [])
                        lyrics_text = "\n".join(lyrics)
                            
        # Clean strings for filesystem
        safe_title = sanitize_filename(title)
        safe_artist = sanitize_filename(artist)
        safe_album = sanitize_filename(album)
        
        # Output paths
        target_dir = output_dir / safe_artist / safe_album
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / f"{safe_title}.mp3"
        
        # Prevent overwriting if file already exists with same name
        # Implement Deduplication Logic based on exact file size
        counter = 1
        is_duplicate = False
        current_target = target_dir / f"{safe_title}.mp3"
        
        while current_target.exists():
            # Check if it's an exact duplicate (using file size for speed)
            if os.path.getsize(input_file) == os.path.getsize(current_target):
                is_duplicate = True
                # Log the duplicate
                log_path = output_dir / "duplicates_log.txt"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"DUPLICATE SKIPPED: '{input_file.absolute()}' is identical to an already organized file at '{current_target.absolute()}'\n")
                
                print(f"  [-] Skipped Duplicate: {input_file.name}. Identical to {current_target.name}")
                return # Skip copying and database insertion completely
            
            # File exists but sizes differ (different version/rip quality), keep both by appending counter
            current_target = target_dir / f"{safe_title} ({counter}).mp3"
            counter += 1
            
        target_path = current_target
            
        # Copy the file
        shutil.copy2(input_file, target_path)
        
        # Update metadata tags
        try:
            audio = EasyID3(target_path)
        except ID3NoHeaderError:
            # File does not have ID3 tags yet, create them safely
            file_mut = mutagen.File(target_path, easy=True)
            if file_mut is None:
                # Fallback if mutagen cannot interpret the file at all natively
                empty_tags = ID3()
                empty_tags.save(target_path)
                file_mut = mutagen.File(target_path, easy=True)
            file_mut.add_tags()
            audio = file_mut
            
        audio['title'] = title
        audio['artist'] = artist
        audio['album'] = album
        audio.save()
        
        # --- Advanced ID3 Tags (Cover Art & Lyrics) ---
        image_data = None
        if cover_art_url:
            image_data = await download_image(cover_art_url)
            
        if image_data or lyrics_text:
            try:
                tags = ID3(target_path)
                if image_data:
                    tags.add(
                        APIC(
                            encoding=3,       # UTF-8
                            mime='image/jpeg',
                            type=3,           # Cover Front
                            desc=u'Cover',
                            data=image_data
                        )
                    )
                if lyrics_text:
                    tags.add(
                        USLT(
                            encoding=3,
                            lang=u'eng',
                            desc=u'Lyrics',
                            text=lyrics_text
                        )
                    )
                tags.save(v2_version=3)
            except Exception as e:
                print(f"      [~] Warning: Could not inject advanced tags: {e}")
        
        # --- Database Insertion ---
        relative_path = os.path.relpath(target_path, output_dir)
        # Standardize path separator for cross-platform portability
        relative_path = Path(relative_path).as_posix()
        
        art_id = database.get_or_create_artist(conn, artist)
        rec_id = database.get_or_create_record(conn, art_id, album, None)
        database.insert_song(conn, rec_id, title, relative_path)
        # --------------------------
        
        print(f"  [+] Recognized and Organized -> {artist} - {title}")
        
        # Mark successful process in Database cache
        try:
            database.mark_file_processed(conn, str(original_file_path), os.path.getsize(original_file_path))
        except Exception:
            pass
        
    except Exception as e:
        print(f"  [X] Error processing {original_file_path.name}: {str(e)}")

async def main_async(input_path, output_path):
    shazam = Shazam()
    input_dir = Path(input_path)
    output_dir = Path(output_path)
    
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Database
    db_path = output_dir / "openmp3id.db"
    database.init_db(db_path)
    conn = database.get_connection(db_path)
    
    # gather all supported audio cases insensitively
    supported_extensions = ("*.mp3", "*.m4a", "*.flac", "*.wav", "*.wma", "*.aac")
    audio_files = []
    for ext in supported_extensions:
        audio_files.extend(list(input_dir.rglob(ext)))
        audio_files.extend(list(input_dir.rglob(ext.upper())))
    
    if not audio_files:
        print("No supported audio files found in the input directory.")
        return
        
    print(f"Found {len(audio_files)} audio files. Starting organization...")
    print(f"Copying and organizing into: {output_dir.absolute()}\n")
    
    # Process files sequentially to avoid rate limiting or overloading Shazam's free API wrapper
    for file in audio_files:
        # Ignore macOS shadow files and hidden files natively
        if file.name.startswith('.'):
            continue
            
        # Check SQLite State Cache before starting expensive operations
        try:
            file_size = os.path.getsize(file)
            if database.is_file_processed(conn, str(file), file_size):
                print(f"Skipping (Already Processed): {file.name}")
                continue
        except Exception:
            pass
            
        is_temp = False
        processing_file = file
        
        if file.suffix.lower() != '.mp3':
            print(f"  [~] Transcoding {file.name} to MP3...")
            try:
                # WMA files sometimes load better if explicitly told 'asf'
                input_format = file.suffix.lower().lstrip('.')
                if input_format == 'wma':
                    input_format = 'asf'
                
                audio = AudioSegment.from_file(str(file), format=input_format)
                fd, temp_path = tempfile.mkstemp(suffix='.mp3')
                os.close(fd)
                
                audio.export(temp_path, format="mp3")
                processing_file = Path(temp_path)
                is_temp = True
            except Exception as e:
                print(f"  [X] Failed to convert {file.name}. Ensure FFmpeg is installed! Error: {str(e)}")
                continue
                
        await process_file(shazam, processing_file, output_dir, conn, original_file_path=file, base_input_dir=input_dir)
        
        if is_temp:
            try:
                os.remove(processing_file)
            except:
                pass
        
    conn.close()
    print("\nOrganization complete! Enjoy your organized library.")

def main():
    parser = argparse.ArgumentParser(description="Auto-organize and tag unidentified MP3 files using Shazam.")
    parser.add_argument("-i", "--input", required=True, help="Path to directory containing input MP3 files")
    parser.add_argument("-o", "--output", required=True, help="Path to output organized directory")
    args = parser.parse_args()
    
    asyncio.run(main_async(args.input, args.output))

if __name__ == "__main__":
    main()
