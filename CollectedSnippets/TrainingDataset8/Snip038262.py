def is_pydeck(obj: object) -> TypeGuard[Deck]:
    """True if input looks like a pydeck chart."""
    return is_type(obj, "pydeck.bindings.deck.Deck")