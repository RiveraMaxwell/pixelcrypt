# PixelCrypt - Image Pixel Encryption Tool

A Python GUI application that encrypts and decrypts images using XOR-based pixel manipulation with a user-provided key.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **XOR Pixel Encryption** — Symmetric encryption using a key-derived pseudorandom keystream
- **Multiple Format Support** — PNG, JPEG, BMP, TIFF input (always outputs lossless PNG)
- **Key Strength Indicator** — Real-time visual feedback on key quality
- **Realtime Preview** — Watch the encryption/decryption process chunk by chunk
- **Side-by-Side Comparison** — View original and processed images together
- **Batch Processing** — Encrypt/decrypt multiple files at once
- **Drag & Drop** — Drop images directly into the application window
- **Round-Trip Verification** — Verify that decryption produces the original image
- **Dark Theme** — Modern dark UI
- **Copy Output Path** — Quick clipboard copy of saved file location

## How It Works

1. Your text key is hashed with SHA-256 and converted to a 32-bit seed
2. A NumPy random generator produces a keystream matching the image dimensions
3. Each pixel is XOR'd with the corresponding keystream value
4. Since XOR is its own inverse, using the same key on an encrypted image restores the original

> ⚠️ This is a demonstration/educational tool. The encryption is not suitable for protecting sensitive data against determined attackers.

## Installation

### Prerequisites

- Python 3.8 or higher

### Setup

```bash
# Clone the repository
git clone https://github.com/RiveraMaxwell/pixelcrypt.git
cd pixelcrypt

# Install dependencies
pip install -r requirements.txt
```

### Optional: Drag & Drop Support

Drag & drop requires `tkinterdnd2`. It's included in requirements.txt but the app works without it.

## Usage

```bash
# Run the application
python src/app.py
```

### Quick Start

1. Click **Browse Image** or drag & drop an image file
2. Enter an encryption key
3. Click **🔒 Encrypt** to encrypt or **🔓 Decrypt** to decrypt
4. The output is saved alongside the original with `_encrypt` or `_decrypt` suffix

### Batch Processing

1. Enter your key
2. Click **📁 Batch Process**
3. Select multiple image files
4. Choose encrypt or decrypt
5. All files are processed with the same key

### Verification

After encrypting, click **✓ Verify** to confirm that decrypting the output with the same key reproduces the original image.

## Live Demo

👉 **[Try it online](https://riveramaxwell.github.io/pixelcrypt/app.html)** — no installation needed, runs entirely in your browser.

## Project Structure

```
pixelcrypt/
├── docs/                  # GitHub Pages website
│   ├── index.html         # Landing page
│   ├── style.css          # Landing page styles
│   ├── app.html           # Web encryption tool
│   ├── app.css            # Web app styles
│   └── app.js             # Client-side encryption engine
├── src/
│   ├── __init__.py
│   ├── app.py             # Python GUI application
│   └── encryption.py      # Python encryption engine
├── requirements.txt
├── LICENSE
├── .gitignore
└── README.md
```

## Important Notes

- **Always use PNG for encrypted output** — JPEG compression is lossy and will corrupt encrypted data, making decryption impossible. The tool automatically saves as PNG.
- **Remember your key** — There is no key recovery. If you lose the key, the image cannot be decrypted.
- **Same key for encrypt and decrypt** — XOR encryption is symmetric.

## Technical Details

| Component | Technology |
|-----------|-----------|
| GUI | Tkinter + ttk |
| Image Processing | Pillow (PIL) |
| Pixel Operations | NumPy |
| Key Derivation | SHA-256 → 32-bit seed |
| RNG | numpy.random.default_rng (PCG64) |
| Cipher | XOR stream cipher |

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
