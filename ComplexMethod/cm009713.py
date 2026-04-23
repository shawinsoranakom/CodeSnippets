def test_mustache_prompt_from_template(snapshot: SnapshotAssertion) -> None:
    """Test prompts can be constructed from a template."""
    # Single input variable.
    template = "This is a {{foo}} test."
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(foo="bar") == "This is a bar test."
    assert prompt.input_variables == ["foo"]
    assert prompt.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {"foo": {"title": "Foo", "type": "string", "default": None}},
    }

    # Multiple input variables.
    template = "This {{bar}} is a {{foo}} test."
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(bar="baz", foo="bar") == "This baz is a bar test."
    assert prompt.input_variables == ["bar", "foo"]
    assert prompt.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {
            "bar": {"title": "Bar", "type": "string", "default": None},
            "foo": {"title": "Foo", "type": "string", "default": None},
        },
    }

    # Multiple input variables with repeats.
    template = "This {{bar}} is a {{foo}} test {{&foo}}."
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(bar="baz", foo="bar") == "This baz is a bar test bar."
    assert prompt.input_variables == ["bar", "foo"]
    assert prompt.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {
            "bar": {"title": "Bar", "type": "string", "default": None},
            "foo": {"title": "Foo", "type": "string", "default": None},
        },
    }

    # Nested variables.
    template = "This {{obj.bar}} is a {{obj.foo}} test {{{foo}}}."
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(obj={"bar": "foo", "foo": "bar"}, foo="baz") == (
        "This foo is a bar test baz."
    )
    assert prompt.input_variables == ["foo", "obj"]
    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(prompt.get_input_jsonschema()) == snapshot(
            name="schema_0"
        )

    # . variables
    template = "This {{.}} is a test."
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(foo="baz") == ("This {'foo': 'baz'} is a test.")
    assert prompt.input_variables == []
    assert prompt.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {},
    }

    # section/context variables
    template = """This{{#foo}}
        {{bar}}
    {{/foo}}is a test."""
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(foo={"bar": "yo"}) == (
        """This
        yo
    is a test."""
    )
    assert prompt.input_variables == ["foo"]
    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(prompt.get_input_jsonschema()) == snapshot(
            name="schema_2"
        )

    # more complex nested section/context variables
    template = """This{{#foo}}
        {{bar}}
        {{#baz}}
            {{qux}}
        {{/baz}}
        {{quux}}
    {{/foo}}is a test."""
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(
        foo={"bar": "yo", "baz": [{"qux": "wassup"}], "quux": "hello"}
    ) == (
        """This
        yo
            wassup
        hello
    is a test."""
    )
    assert prompt.input_variables == ["foo"]
    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(prompt.get_input_jsonschema()) == snapshot(
            name="schema_3"
        )

    # triply nested section/context variables
    template = """This{{#foo}}
        {{bar}}
        {{#baz.qux}}
            {{#barfoo}}
                {{foobar}}
            {{/barfoo}}
            {{foobar}}
        {{/baz.qux}}
        {{quux}}
    {{/foo}}is a test."""
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(
        foo={
            "bar": "yo",
            "baz": {
                "qux": [
                    {"foobar": "wassup"},
                    {"foobar": "yoyo", "barfoo": {"foobar": "hello there"}},
                ]
            },
            "quux": "hello",
        }
    ) == (
        """This
        yo
            wassup
                hello there
            yoyo
        hello
    is a test."""
    )
    assert prompt.input_variables == ["foo"]
    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(prompt.get_input_jsonschema()) == snapshot(
            name="schema_4"
        )

    # section/context variables with repeats
    template = """This{{#foo}}
        {{bar}}
    {{/foo}}is a test."""
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format(foo=[{"bar": "yo"}, {"bar": "hello"}]) == (
        """This
        yo

        hello
    is a test."""  # noqa: W293
    )
    assert prompt.input_variables == ["foo"]
    if PYDANTIC_VERSION_AT_LEAST_29:
        assert _normalize_schema(prompt.get_input_jsonschema()) == snapshot(
            name="schema_5"
        )
    template = """This{{^foo}}
        no foos
    {{/foo}}is a test."""
    prompt = PromptTemplate.from_template(template, template_format="mustache")
    assert prompt.format() == (
        """This
        no foos
    is a test."""
    )
    assert prompt.input_variables == ["foo"]
    assert _normalize_schema(prompt.get_input_jsonschema()) == {
        "properties": {"foo": {"title": "Foo", "type": "object"}},
        "title": "PromptInput",
        "type": "object",
    }