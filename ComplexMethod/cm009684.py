def test_mmr_from_examples() -> None:
    examples = [{"foo": "bar"}]
    embeddings = FakeEmbeddings(size=1)
    selector = MaxMarginalRelevanceExampleSelector.from_examples(
        examples=examples,
        embeddings=embeddings,
        vectorstore_cls=DummyVectorStore,
        k=2,
        fetch_k=5,
        input_keys=["foo"],
        example_keys=["some_example_key"],
        vectorstore_kwargs={"vs_foo": "vs_bar"},
        init_arg="some_init_arg",
    )
    assert selector.input_keys == ["foo"]
    assert selector.example_keys == ["some_example_key"]
    assert selector.k == 2
    assert selector.fetch_k == 5
    assert selector.vectorstore_kwargs == {"vs_foo": "vs_bar"}

    assert isinstance(selector.vectorstore, DummyVectorStore)
    vector_store = selector.vectorstore
    assert vector_store.embeddings is embeddings
    assert vector_store.init_arg == "some_init_arg"
    assert vector_store.texts == ["bar"]
    assert vector_store.metadatas == [{"foo": "bar"}]