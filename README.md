# openMP3id

openMP3id is an automated Python agent that identifies your unnamed or untagged MP3, WMA, M4A, FLAC, and WAV files by "listening" to them using audio fingerprinting. It automatically transcodes any irregular formats into standard MP3s on the fly, retrieves pristine metadata (Artist, Album, Title) from the Shazam API, writes those ID3 tags (including Album Art and Lyrics) permanently, and copies them into a beautifully structured `<Artist>/<Album>/<Song Name>.mp3` folder hierarchy.

## Features
- **Audio Fingerprinting**: Uses `shazamio` to identify songs regardless of their current filename.
- **Zero Data Loss**: Safely **copies** the identified songs to a new directory instead of overwriting, ensuring your original collection remains perfectly intact.
- **Multi-Format Transcoding**: Automatically universally accepts `.wma`, `.m4a`, `.flac`, and `.wav` formats and natively transforms them into standard `mp3` files behind the scenes using `FFmpeg`.
- **Auto ID3 Tagging & Embellishment**: Imprints retrieved data directly into the file's ID3 wrapper using `mutagen`, including injecting visual Album Art cover images and transcription Lyrics directly into the `.mp3`.
- **Intelligent Sorting**: Moves any unidentified tracks into an `Unknown` directory for easy manual curation.
- **Movable SQLite Database**: Automatically constructs an `openmp3id.db` relational database tracking Artists, Albums, and Songs directly in your destination folder. It uses relative paths, making your entire music library and database 100% portable.

## 🐳 Recommended Usage: Docker

Because multi-format conversion requires `FFmpeg` (which is notoriously tricky to configure on native Windows), the most robust and secure way to run `openMP3id` is via Docker. This keeps your host machine completely clean.

1. **Build the Container Image:**
   ```bash
   docker build -t openmp3id .
   ```
2. **Run it:**
   Mount your local messy music folder directly to `/input_music`, and your desired output folder to `/organized_library`.
   ```bash
   docker run -v "C:\Path\To\Raw\Music:/input_music" -v "C:\Path\To\Output:/organized_library" openmp3id
   ```

## Native Python Installation

Ensure you have Python 3.10+ installed. You **must also manually install FFmpeg** and add it to your System PATH variables to process non-mp3 files!

Then, from the project directory, install the required dependencies:

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
