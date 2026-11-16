"""
Authentication Manager, Token Security & Rate Limiting.
Provides salted password hashing (PBKDF2-HMAC-SHA256), signed session tokens,
role-based permissions (Operator vs Facility Admin), and API rate limiting.
"""

import hashlib
import os
import hmac
import time
from typing import Dict, Any, Optional, Tuple

class SecurityAuthManager:
    SECRET_KEY = os.environ.get("NEXUS_SECRET_KEY", "nexus-industrial-workcell-key-2026-secure-salt")
    SALT = b"nexus_salt_secure_2026"
    ITERATIONS = 100_000

    def __init__(self):
        # In-memory Rate Limiting (IP/Client -> list of timestamps)
        self.rate_limit_records: Dict[str, list] = {}
        self.MAX_REQUESTS_PER_MINUTE = 120

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """Derives a secure, salted PBKDF2-HMAC-SHA256 password hash."""
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            cls.SALT,
            cls.ITERATIONS
        )
        return derived.hex()

    @classmethod
    def verify_password(cls, plain_password: str, hashed_hex: str) -> bool:
        """Constant-time password comparison to prevent timing attacks."""
        calculated = cls.hash_password(plain_password)
        return hmac.compare_digest(calculated, hashed_hex)

    @classmethod
    def generate_signed_token(cls, user_id: str, role: str = "operator") -> str:
        """Generates an HMAC-SHA256 signed operational token."""
        timestamp = int(time.time())
        payload = f"{user_id}:{role}:{timestamp}"
        signature = hmac.new(
            cls.SECRET_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f"{payload}:{signature}"

    @classmethod
    def verify_signed_token(cls, token: str, max_age_seconds: int = 86400) -> Tuple[bool, Optional[str], Optional[str]]:
        """Verifies integrity, signature, and expiration of an operational token."""
        try:
            parts = token.split(":")
            if len(parts) != 4:
                return False, None, None

            user_id, role, timestamp_str, received_sig = parts
            timestamp = int(timestamp_str)

            # Check expiration
            if time.time() - timestamp > max_age_seconds:
                return False, None, None

            payload = f"{user_id}:{role}:{timestamp}"
            expected_sig = hmac.new(
                cls.SECRET_KEY.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(expected_sig, received_sig):
                return True, user_id, role
            return False, None, None
        except Exception:
            return False, None, None

    def check_rate_limit(self, client_id: str) -> bool:
        """
        Sliding-window rate limiter. Returns True if request is allowed,
        False if client has exceeded threshold.
        """
        now = time.time()
        window_start = now - 60.0

        if client_id not in self.rate_limit_records:
            self.rate_limit_records[client_id] = []

        # Filter out requests older than 60 seconds
        self.rate_limit_records[client_id] = [
            ts for ts in self.rate_limit_records[client_id] if ts > window_start
        ]

        if len(self.rate_limit_records[client_id]) >= self.MAX_REQUESTS_PER_MINUTE:
            return False

        self.rate_limit_records[client_id].append(now)
        return True
