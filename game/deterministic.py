import hashlib


def seed_from_parts(*parts) -> int:
    """Build a stable 32-bit seed from arbitrary deterministic inputs."""
    raw = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest, 16) % (2 ** 32)