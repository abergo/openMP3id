import os
import shutil
import asyncio
import argparse
from pathlib import Path
import re
from shazamio import Shazam
from mutagen.easyid3 import EasyID3
import mutagen
from mutagen.id3 import ID3NoHeaderError

def sanitize_filename(name):
    # Remove characters that are problematic in filenames on Windows/Linux/Mac
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

async def process_file(shazam, input_file, output_dir):
    print(f"Processing: {input_file.name}")
    try:
        # identify the song
        out = await shazam.recognize(str(input_file))
        
        if 'track' not in out:
            print(f"  [!] Could not recognize {input_file.name}. Moving to Unknown.")
            unknown_dir = output_dir / "Unknown"
            unknown_dir.mkdir(parents=True, exist_ok=True)
            target_path = unknown_dir / input_file.name
            shutil.copy2(input_file, target_path)
            return
            
        track = out['track']
        title = track.get('title', 'Unknown Title')
        artist = track.get('subtitle', 'Unknown Artist')
        
        # Extract Album if available
        album = "Unknown Album"
        if 'sections' in track:
            for section in track['sections']:
                if section.get('type') == 'SONG':
                    for meta in section.get('metadata', []):
                        if meta.get('title') == 'Album':
                            album = meta.get('text')
                            break
                            
        # Clean strings for filesystem
        safe_title = sanitize_filename(title)
        safe_artist = sanitize_filename(artist)
        safe_album = sanitize_filename(album)
        
        # Output paths
        target_dir = output_dir / safe_artist / safe_album
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = target_dir / f"{safe_title}.mp3"
        
        # Prevent overwriting if file already exists with same name
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{safe_title} ({counter}).mp3"
            counter += 1
            
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
                from mutagen.id3 import ID3
                empty_tags = ID3()
                empty_tags.save(target_path)
                file_mut = mutagen.File(target_path, easy=True)
            file_mut.add_tags()
            audio = file_mut
            
        audio['title'] = title
        audio['artist'] = artist
        audio['album'] = album
        audio.save()
        
        print(f"  [+] Recognized and Organized -> {artist} - {title}")
        
    except Exception as e:
        print(f"  [X] Error processing {input_file.name}: {str(e)}")

async def main_async(input_path, output_path):
    shazam = Shazam()
    input_dir = Path(input_path)
    output_dir = Path(output_path)
    
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # gather all mp3 cases insensitively
    mp3_files = list(input_dir.rglob("*.[mM][pP]3"))
    
    if not mp3_files:
        print("No MP3 files found in the input directory.")
        return
        
    print(f"Found {len(mp3_files)} MP3 files. Starting organization...")
    print(f"Copying and organizing into: {output_dir.absolute()}\n")
    
    # Process files sequentially to avoid rate limiting or overloading Shazam's free API wrapper
    for file in mp3_files:
        await process_file(shazam, file, output_dir)
        
    print("\nOrganization complete! Enjoy your organized library.")

def main():
    parser = argparse.ArgumentParser(description="Auto-organize and tag unidentified MP3 files using Shazam.")
    parser.add_argument("-i", "--input", required=True, help="Path to directory containing input MP3 files")
    parser.add_argument("-o", "--output", required=True, help="Path to output organized directory")
    args = parser.parse_args()
    
    asyncio.run(main_async(args.input, args.output))

if __name__ == "__main__":
    main()
