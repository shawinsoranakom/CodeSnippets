def test_configurable_fields(snapshot: SnapshotAssertion) -> None:
    fake_llm = FakeListLLM(responses=["a"])  # str -> list[list[str]]

    assert fake_llm.invoke("...") == "a"

    fake_llm_configurable = fake_llm.configurable_fields(
        responses=ConfigurableField(
            id="llm_responses",
            name="LLM Responses",
            description="A list of fake responses for this LLM",
        )
    )

    assert fake_llm_configurable.invoke("...") == "a"

    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(
            fake_llm_configurable.get_config_jsonschema()
        ) == snapshot(name="schema2")

    fake_llm_configured = fake_llm_configurable.with_config(
        configurable={"llm_responses": ["b"]}
    )

    assert fake_llm_configured.invoke("...") == "b"

    prompt = PromptTemplate.from_template("Hello, {name}!")

    assert prompt.invoke({"name": "John"}) == StringPromptValue(text="Hello, John!")

    prompt_configurable = prompt.configurable_fields(
        template=ConfigurableField(
            id="prompt_template",
            name="Prompt Template",
            description="The prompt template for this chain",
        )
    )

    assert prompt_configurable.invoke({"name": "John"}) == StringPromptValue(
        text="Hello, John!"
    )

    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(
            prompt_configurable.get_config_jsonschema()
        ) == snapshot(name="schema3")

    prompt_configured = prompt_configurable.with_config(
        configurable={"prompt_template": "Hello, {name}! {name}!"}
    )

    assert prompt_configured.invoke({"name": "John"}) == StringPromptValue(
        text="Hello, John! John!"
    )

    assert prompt_configurable.with_config(
        configurable={"prompt_template": "Hello {name} in {lang}"}
    ).get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {
            "lang": {"title": "Lang", "type": "string"},
            "name": {"title": "Name", "type": "string"},
        },
        "required": ["lang", "name"],
    }

    chain_configurable = prompt_configurable | fake_llm_configurable | StrOutputParser()

    assert chain_configurable.invoke({"name": "John"}) == "a"

    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(
            chain_configurable.get_config_jsonschema()
        ) == snapshot(name="schema4")

    assert (
        chain_configurable.with_config(
            configurable={
                "prompt_template": "A very good morning to you, {name} {lang}!",
                "llm_responses": ["c"],
            }
        ).invoke({"name": "John", "lang": "en"})
        == "c"
    )

    assert chain_configurable.with_config(
        configurable={
            "prompt_template": "A very good morning to you, {name} {lang}!",
            "llm_responses": ["c"],
        }
    ).get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {
            "lang": {"title": "Lang", "type": "string"},
            "name": {"title": "Name", "type": "string"},
        },
        "required": ["lang", "name"],
    }

    chain_with_map_configurable: Runnable = prompt_configurable | {
        "llm1": fake_llm_configurable | StrOutputParser(),
        "llm2": fake_llm_configurable | StrOutputParser(),
        "llm3": fake_llm.configurable_fields(
            responses=ConfigurableField("other_responses")
        )
        | StrOutputParser(),
    }

    assert chain_with_map_configurable.invoke({"name": "John"}) == {
        "llm1": "a",
        "llm2": "a",
        "llm3": "a",
    }

    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(
            chain_with_map_configurable.get_config_jsonschema()
        ) == snapshot(name="schema5")

    assert chain_with_map_configurable.with_config(
        configurable={
            "prompt_template": "A very good morning to you, {name}!",
            "llm_responses": ["c"],
            "other_responses": ["d"],
        }
    ).invoke({"name": "John"}) == {"llm1": "c", "llm2": "c", "llm3": "d"}