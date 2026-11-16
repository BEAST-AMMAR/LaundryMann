"""
Input Validation & Security Sanitizer.
Protects against malicious payloads, file upload vulnerabilities,
decompression bombs, MIME spoofing, and metadata leakage.
"""

import io
from PIL import Image
import numpy as np
from typing import Tuple, Optional

class SecurityValidator:
    MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB Cap
    MAX_IMAGE_DIMENSION = 4096             # Max 4096 x 4096 pixels (Decompression bomb guard)
    ALLOWED_MIMES = ["image/jpeg", "image/png", "image/webp"]

    @staticmethod
    def validate_and_sanitize_image(raw_bytes: bytes) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Validates file size, inspects magic bytes, checks dimensions,
        and sanitizes the image by stripping all EXIF metadata.
        Returns: (is_valid, sanitized_numpy_rgb, error_message)
        """
        # 1. File Size Verification
        if len(raw_bytes) == 0:
            return False, None, "File payload is empty (0 bytes)."

        if len(raw_bytes) > SecurityValidator.MAX_FILE_SIZE_BYTES:
            return False, None, f"File exceeds maximum allowed limit of 8 MB (received {len(raw_bytes)/(1024*1024):.2f} MB)."

        # 2. Magic Bytes Verification
        is_jpeg = raw_bytes[:3] == b'\xff\xd8\xff'
        is_png = raw_bytes[:8] == b'\x89PNG\r\n\x1a\n'
        is_webp = len(raw_bytes) > 12 and raw_bytes[:4] == b'RIFF' and raw_bytes[8:12] == b'WEBP'

        if not (is_jpeg or is_png or is_webp):
            return False, None, "Security Violation: Invalid file signature. Only authentic JPEG, PNG, and WebP images are permitted."

        # 3. Decompression Bomb & Integrity Check
        try:
            with Image.open(io.BytesIO(raw_bytes)) as pil_img:
                width, height = pil_img.size
                if width > SecurityValidator.MAX_IMAGE_DIMENSION or height > SecurityValidator.MAX_IMAGE_DIMENSION:
                    return False, None, f"Image dimensions {width}x{height} exceed maximum security threshold of {SecurityValidator.MAX_IMAGE_DIMENSION}px."

                # 4. EXIF Stripping & Sanitization
                # Re-encoding into raw RGB numpy array completely strips all EXIF metadata, GPS, and serial tags
                rgb_img = pil_img.convert('RGB')
                sanitized_array = np.array(rgb_img)
                return True, sanitized_array, "OK"

        except Exception as e:
            return False, None, f"Image decoding integrity failure: {e}"

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 120) -> str:
        """Sanitizes user/operator text inputs against command injection and XSS."""
        if not input_str:
            return ""
        # Strip dangerous characters
        cleaned = "".join(ch for ch in input_str if ch.isalnum() or ch in " _-.,/:()[]").strip()
        return cleaned[:max_length]
