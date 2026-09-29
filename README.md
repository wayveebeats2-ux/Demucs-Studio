# Demucs Studio

**A modern, Windows-focused desktop studio for AI-powered stem separation.**

Demucs Studio is a fork of **Demucs GUI by Carl Gao**, rebuilt around a darker DAW-inspired workflow while preserving the proven Demucs separation backend.

> **Project status:** active development. The modern Studio interface is usable, but releases and some workflow features are still being built and tested.

## What Demucs Studio adds

- Modern dark Studio interface with GPU/device status
- Drag-and-drop track importing
- Embedded metadata and album artwork
- 4-stem, Vocals + Instrumental, and 6-stem workflows
- CUDA-accelerated Demucs processing where supported
- Configurable segment, overlap, shifts, input gain and output depth
- Configurable output directory and collision handling
- Real waveform previews for completed stems
- Click/drag waveform seeking and a seekable main timeline
- Live synchronized stem auditioning with Solo, Mute and gain controls
- Resizable expanded waveform views
- Offline audition-mix export
- Persistent separation Library with search and folder scanning
- **DrumSep secondary separation:** right-click a separated Drums waveform and split it further into **Kick, Snare, Cymbals and Toms**
- Expandable Drum sub-stems with an independent drum-only audition mixer

## DrumSep workflow

Demucs Studio treats drum refinement as a second-stage operation rather than a normal full-song model.

1. Separate a track normally.
2. Right-click the **Drums** waveform.
3. Choose **Separate Drums Further…**.
4. On first use, Demucs Studio downloads and verifies the DrumSep checkpoint.
5. The Drums row gains an expandable child section containing:
   - Kick
   - Snare
   - Cymbals
   - Toms

The child stems use their own audition mixer, so they are **not doubled into the main Vocals / Drums / Bass / Other mix**.

DrumSep's native model source names are translated for the Studio UI. Hi-hat material is included in the Cymbals stem rather than provided as a separate output.

## Running the Studio interface from source

The current development target is Windows with Python 3.11.

Clone the repository and create/activate a virtual environment, then install the project dependencies. For the CUDA build, install a CUDA-enabled PyTorch version appropriate for your NVIDIA GPU.

FFmpeg and FFprobe should be available on your system `PATH`.

Launch the modern interface with:

```powershell
python GUI\StudioMain.py
```

The original upstream interface remains available as:

```powershell
python GUI\GuiMain.py
```

### Example tested development environment

Demucs Studio is currently being developed and tested with:

- Windows 10/11
- Python 3.11
- NVIDIA CUDA acceleration
- PyTorch CUDA build
- FFmpeg
- PySide6 / Qt Multimedia

CPU operation remains available through the inherited Demucs backend, although GPU acceleration is strongly preferable for separation speed.

## Current Studio structure

```text
GUI/
├── StudioMain.py
├── GuiMain.py                 # original/upstream GUI entry point
├── separator.py               # Demucs backend
├── audio.py
├── shared.py
└── ui/
    ├── main_window.py
    ├── controller.py
    ├── stem_results.py
    ├── audition.py
    ├── waveform.py
    ├── media_info.py
    ├── library_store.py
    ├── library_view.py
    ├── drop_zone.py
    └── theme.py
```

The Studio UI is intentionally kept separate from the separation backend so UI work does not require replacing the existing Demucs inference pipeline.

## Development roadmap

Current priorities include:

- Settings page and persistent Studio preferences
- More robust DrumSep progress/model-management UI
- Playback synchronization refinements
- Library detail/reconnect tools
- Model download/cache management
- Cancellation and queue improvements
- Diagnostics/logging
- UI polish and accessibility
- Packaging and first Demucs Studio release

## Upstream project and attribution

Demucs Studio is a fork of **[Demucs GUI](https://github.com/CarlGao4/Demucs-Gui)** by **Carl Gao**. The upstream project provides the core GUI/backend foundation this project was built from.

The separation engine is based on **[Demucs](https://github.com/adefossez/demucs)**.

Please support and credit the upstream projects. Their work made Demucs Studio possible.

## License

This repository retains the upstream **GPL-3.0 license**. See [LICENSE](LICENSE) for details.

Third-party components and models remain subject to their respective licenses and terms.

## Acknowledgements

- **Carl Gao** — Demucs GUI
- **Alexandre Défossez and Demucs contributors** — Demucs
- **DrumSep contributors** — secondary drum-stem separation model
- The PyTorch, Qt/PySide and FFmpeg projects

---

**Demucs Studio** — AI-powered stem separation with a workflow built for actually working with the stems.
