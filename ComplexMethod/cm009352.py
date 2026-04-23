def test_groq_serialization() -> None:
    """Test that ChatGroq can be successfully serialized and deserialized."""
    api_key1 = "top secret"
    api_key2 = "topest secret"
    llm = ChatGroq(model="foo", api_key=api_key1, temperature=0.5)  # type: ignore[call-arg, arg-type]
    dump = lc_load.dumps(llm)
    llm2 = lc_load.loads(
        dump,
        valid_namespaces=["langchain_groq"],
        secrets_map={"GROQ_API_KEY": api_key2},
        allowed_objects="all",
    )

    assert type(llm2) is ChatGroq

    # Ensure api key wasn't dumped and instead was read from secret map.
    assert llm.groq_api_key is not None
    assert llm.groq_api_key.get_secret_value() not in dump
    assert llm2.groq_api_key is not None
    assert llm2.groq_api_key.get_secret_value() == api_key2

    # Ensure a non-secret field was preserved
    assert llm.temperature == llm2.temperature

    # Ensure a None was preserved
    assert llm.groq_api_base == llm2.groq_api_base