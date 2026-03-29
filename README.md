# InternetMetr (PyQt6)

Desktop application that monitors network interfaces, local/public IP and internet speed.

## Architecture

The project follows clean architecture with a component-style UI.

- `domain`: entities and abstract ports
- `application`: use-cases
- `infrastructure`: OS/network adapters
- `presentation`: PyQt6 UI components and view-model

## Current platform support

- Windows: implemented adapter
- Linux/macOS: placeholders for future implementation

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
internetmetr
```

## Notes

- Public IP is requested from `https://api.ipify.org`.
- Speed test uses `speedtest-cli` package and may take a few seconds.
