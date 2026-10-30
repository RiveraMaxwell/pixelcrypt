# PixelCrypt

PixelCrypt is an educational image-scrambling tool with a Python desktop app and a browser app. Both use
key-derived XOR streams, but their pseudorandom generators are different, so files encrypted by one version
are not interchangeable with the other.

This is not modern cryptography and should not be used to protect sensitive images.

## Browser app

Open `docs/index.html` through GitHub Pages or a local static server. The browser version processes images
locally and does not upload them. It supports PNG, JPEG, BMP, and TIFF input, always downloads PNG output,
and can encrypt, decrypt, preview, verify, and download an image.

For a quick local server:

```bash
python -m http.server 8000 --directory docs
```

Then open <http://localhost:8000/>.

## Python desktop app

Requires Python 3.8 or newer.

```bash
pip install -r requirements.txt
python src/app.py
```

The desktop app supports image selection, optional drag and drop, realtime preview, batch processing, round-trip
verification, and copying the saved output path. Input formats are PNG, JPEG, BMP, and TIFF; output is always
saved as PNG so lossy JPEG compression does not break round trips.

## How it works

1. The key is hashed with SHA-256 and reduced to a 32-bit seed.
2. A deterministic pseudorandom generator creates one byte per RGB channel.
3. Each RGB channel is XORed with the corresponding stream byte.
4. Applying the same operation again restores the original because XOR is self-inverse.

The browser uses a small xoshiro-based generator. The desktop app uses NumPy's PCG64 generator, so each version
can decrypt its own output but not the other's.

## Project layout

- `docs/index.html`, `docs/style.css` — landing page.
- `docs/app.html`, `docs/app.css`, `docs/app.js` — browser application.
- `src/app.py` — Tkinter desktop interface.
- `src/encryption.py` — desktop image processing and key-strength logic.
- `requirements.txt` — Python dependencies.

## Limitations

- XOR with a deterministic keystream is for demonstration, not secure encryption.
- Losing the key makes an image unrecoverable.
- The browser and desktop apps use different pseudorandom generators and cannot exchange encrypted files.

## License

MIT. See [LICENSE](LICENSE).
