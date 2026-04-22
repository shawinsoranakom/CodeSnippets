def _generate_scriptrun_id() -> str:
    """Randomly generate a unique ID for a script execution."""
    return str(uuid.uuid4())