from uuid import UUID, uuid4


def generate_id() -> UUID:
    """Generate all internal resource IDs in one place."""
    return uuid4()
