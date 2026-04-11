# Project Context (Gemini)

This project was built to solve the user's problem of having a massive library of entirely unnamed MP3 files. The goal was to construct an autonomous agent built with Python to act as a hyper-efficient librarian. 

## Technical Foundation
- The script uses `shazamio` to asynchronously query an audio fingerprint against the Shazam API.
- We opted against external commercial tools requiring API keys (like ACRCloud) or heavier DB-driven local fingerprinting (like Dejavu) for a lightweight, zero-configuration setup. If Shazam struggles in the future, `pyacoustid` (using the MusicBrainz database) is noted as the strongest open-source fallback candidate.
- `mutagen.easyid3.EasyID3` was chosen as the workhorse for rewriting MP3 metadata natively, preventing data corruption while injecting proper ID3 tags back into the respective file.
- The agent utilizes `asyncio` to handle identifying files quickly and gracefully without locking the main thread.
- By user request, we designed the agent to act non-destructively: it strictly copies items to an output schema `<Artist>/<Album>/<Title.mp3>` rather than overwriting original files, serving as an ultimate fail-safe against the engine misidentifying remixes, bootlegs, or live cover matches.
