def _assert_entry(
    entry, when=None, name=None, message=None, domain=None, entity_id=None, state=None
):
    """Assert an entry is what is expected."""
    if when is not None:
        assert when.isoformat() == entry["when"]

    if name is not None:
        assert name == entry["name"]

    if message is not None:
        assert message == entry["message"]

    if domain is not None:
        assert domain == entry["domain"]

    if entity_id is not None:
        assert entity_id == entry["entity_id"]

    if state is not None:
        assert state == entry["state"]