# openMP3id

openMP3id is an automated Python agent that identifies your unnamed or untagged MP3, WMA, M4A, FLAC, and WAV files by "listening" to them using audio fingerprinting. It automatically transcodes any irregular formats into standard MP3s on the fly, retrieves pristine metadata (Artist, Album, Title) from the Shazam API, writes those ID3 tags (including Album Art and Lyrics) permanently, and copies them into a beautifully structured `<Artist>/<Album>/<Song Name>.mp3` folder hierarchy.

## Features
- **Audio Fingerprinting**: Uses `shazamio` to identify songs regardless of their current filename.
- **Zero Data Loss**: Safely **copies** the identified songs to a new directory instead of overwriting, ensuring your original collection remains perfectly intact.
- **Multi-Format Transcoding**: Automatically universally accepts `.wma`, `.m4a`, `.flac`, and `.wav` formats and natively transforms them into standard `mp3` files behind the scenes using `FFmpeg`.
- **Auto ID3 Tagging & Embellishment**: Imprints retrieved data directly into the file's ID3 wrapper using `mutagen`, including injecting visual Album Art cover images and transcription Lyrics directly into the `.mp3`.
- **Intelligent Sorting**: Moves any unidentified tracks into an `Unknown` directory for easy manual curation.
- **Movable SQLite Database**: Automatically constructs an `openmp3id.db` relational database tracking Artists, Albums, and Songs directly in your destination folder. It uses relative paths, making your entire music library and database 100% portable.

## 🚀 Quick Start (Interactive Wizard)

The fastest and safest way to run the agent is using our zero-dependency interactive launcher. Simply open your terminal and run:

```bash
python start.py
```

The CLI wizard will boot up and ask you to select how you want to run the engine:

1. **🐳 Docker Secure Container (Highly Recommended)**
   - The wizard will ask you to paste your Input and Output paths, automatically build the `FFmpeg` container, and securely execute the pipeline via volume-mounts. Your main computer remains totally unpolluted!
   
2. **🐍 Native Python Virtual Environment**
   - The wizard will instantly construct an isolated workspace (`venv/`), discreetly install all dependencies into it, request your audio paths, and trigger the logic securely underneath.
   - *Note: To process non-MP3 files (like WMA or FLAC) via Native Mode, you must ensure `FFmpeg` is installed on your host computer.*

## Manual Execution (Advanced)

If you prefer to bypass the UI Wizard and type out your mounting paths manually, you can trigger the python engine natively.

Ensure you have Python 3.10+ installed. Install the required dependencies:
```bash
pip install -r requirements.txt
```

Run the core script by passing the path containing your raw loose files `-i`, and the output path `-o`:
```bash
python organizer.py -i "C:\Users\username\Desktop\raw_music" -o "C:\Users\username\Desktop\organized_library"
```
