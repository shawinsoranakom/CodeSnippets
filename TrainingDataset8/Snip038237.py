def is_type(
    obj: object, fqn_type_pattern: Literal["pydeck.bindings.deck.Deck"]
) -> TypeGuard[Deck]:
    ...