def assert_result_info(
    info: template.RenderInfo,
    result: Any,
    entities: Iterable[str] | None = None,
    domains: Iterable[str] | None = None,
    all_states: bool = False,
) -> None:
    """Check result info."""
    actual = info.result()
    assert actual == result, (
        f"Template result mismatch:\n"
        f"  Expected: {result!r} (type: {type(result).__name__})\n"
        f"  Actual:   {actual!r} (type: {type(actual).__name__})\n"
        f"  Template: {info.template!r}"
    )
    assert info.all_states == all_states
    assert info.filter("invalid_entity_name.somewhere") == all_states
    if entities is not None:
        assert info.entities == frozenset(entities)
        assert all(info.filter(entity) for entity in entities)
        if not all_states:
            assert not info.filter("invalid_entity_name.somewhere")
    else:
        assert not info.entities
    if domains is not None:
        assert info.domains == frozenset(domains)
        assert all(info.filter(domain + ".entity") for domain in domains)
    else:
        assert not hasattr(info, "_domains")