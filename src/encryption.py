"""
Image encryption/decryption engine using XOR-based pixel manipulation.
"""

import hashlib
import numpy as np
from PIL import Image


def key_to_seed(key: str) -> int:
    """Convert a string key to a deterministic 32-bit seed using SHA-256."""
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**32)


def compute_image_hash(img: Image.Image) -> str:
    """Compute SHA-256 hash of image pixel data for verification."""
    return hashlib.sha256(np.array(img).tobytes()).hexdigest()


def evaluate_key_strength(key: str) -> tuple[int, str]:
    """
    Evaluate the strength of an encryption key.
    Returns (score 0-100, label).
    """
    if not key:
        return 0, "Empty"

    score = 0
    length = len(key)

    # Length scoring
    if length >= 16:
        score += 40
    elif length >= 12:
        score += 30
    elif length >= 8:
        score += 20
    elif length >= 4:
        score += 10

    # Character variety
    has_lower = any(c.islower() for c in key)
    has_upper = any(c.isupper() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(not c.isalnum() for c in key)

    variety = sum([has_lower, has_upper, has_digit, has_special])
    score += variety * 15

    # Penalize repetitive patterns
    unique_chars = len(set(key))
    if unique_chars < length * 0.5:
        score -= 15

    score = max(0, min(100, score))

    if score >= 80:
        label = "Strong"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Fair"
    elif score >= 20:
        label = "Weak"
    else:
        label = "Very Weak"

    return score, label


def process_image(
    img: Image.Image,
    key: str,
    progress_callback=None,
    preview_callback=None,
    realtime: bool = False,
) -> Image.Image:
    """
    Encrypt or decrypt an image using XOR with a key-derived keystream.

    Args:
        img: PIL Image to process (will be converted to RGB).
        key: Encryption/decryption key string.
        progress_callback: Optional callable(percent: float) for progress updates.
        preview_callback: Optional callable(img: Image) for realtime preview.
        realtime: If True, process in chunks with preview updates.

    Returns:
        Processed PIL Image.
    """
    img = img.convert("RGB")
    img_array = np.array(img, dtype=np.uint8)

    h, w, _ = img_array.shape
    seed = key_to_seed(key)

    rng = np.random.default_rng(seed)
    keystream = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)

    if realtime and preview_callback:
        result = np.empty_like(img_array)
        chunk_size = max(1, h // 50)

        for y in range(0, h, chunk_size):
            y_end = min(h, y + chunk_size)
            result[y:y_end] = np.bitwise_xor(img_array[y:y_end], keystream[y:y_end])

            preview_img = Image.fromarray(result)
            preview_callback(preview_img)

            if progress_callback:
                progress_callback((y_end / h) * 100)
    else:
        result = np.bitwise_xor(img_array, keystream)
        if progress_callback:
            progress_callback(100)

    return Image.fromarray(result)
