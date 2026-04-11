# openMP3id

openMP3id is an automated Python script that identifies your unnamed or untagged MP3 files by "listening" to them using audio fingerprinting. It retrieves correct metadata (Artist, Album, Title) from the Shazam API, writes those ID3 tags permanently into the MP3 file, and copies them into a beautifully structured `<Artist>/<Album>/<Song Name>.mp3` folder hierarchy.

## Features
- **Audio Fingerprinting**: Uses `shazamio` to identify songs regardless of their current filename.
- **Zero Data Loss**: Safely **copies** the identified songs to a new directory instead of overwriting, ensuring your original collection remains perfectly intact.
- **Auto ID3 Tagging**: Imprints the retrieved data straight into the file's ID3 metadata using `mutagen`.
- **Intelligent Sorting**: Moves any unidentified tracks into an `Unknown` directory for easy manual curation.
- **Movable SQLite Database**: Automatically constructs an `openmp3id.db` relational database tracking Artists, Albums, and Songs directly in your destination folder. It uses relative paths, making your entire music library and database 100% portable.

## Installation

Ensure you have Python 3.7+ installed. Then, from the project directory, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the script via command line by passing the path containing your raw loose files, and the output path where you want the structured library built:

```bash
python organizer.py -i "/path/to/raw_mp3s" -o "/path/to/output_folder"
```

**Example:**
```bash
python organizer.py -i "C:\Users\username\Desktop\raw_music" -o "C:\Users\username\Desktop\organized_library"
```
