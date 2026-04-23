def test_schemas(snapshot: SnapshotAssertion) -> None:
    fake = FakeRunnable()  # str -> int

    assert fake.get_input_jsonschema() == {
        "title": "FakeRunnableInput",
        "type": "string",
    }
    assert fake.get_output_jsonschema() == {
        "title": "FakeRunnableOutput",
        "type": "integer",
    }
    assert fake.get_config_jsonschema(include=["tags", "metadata", "run_name"]) == {
        "properties": {
            "metadata": {
                "default": None,
                "title": "Metadata",
                "type": "object",
            },
            "run_name": {"default": None, "title": "Run Name", "type": "string"},
            "tags": {
                "default": None,
                "items": {"type": "string"},
                "title": "Tags",
                "type": "array",
            },
        },
        "title": "FakeRunnableConfig",
        "type": "object",
    }

    fake_bound = FakeRunnable().bind(a="b")  # str -> int

    assert fake_bound.get_input_jsonschema() == {
        "title": "FakeRunnableInput",
        "type": "string",
    }
    assert fake_bound.get_output_jsonschema() == {
        "title": "FakeRunnableOutput",
        "type": "integer",
    }

    fake_w_fallbacks = FakeRunnable().with_fallbacks((fake,))  # str -> int

    assert fake_w_fallbacks.get_input_jsonschema() == {
        "title": "FakeRunnableInput",
        "type": "string",
    }
    assert fake_w_fallbacks.get_output_jsonschema() == {
        "title": "FakeRunnableOutput",
        "type": "integer",
    }

    def typed_lambda_impl(x: str) -> int:
        return len(x)

    typed_lambda = RunnableLambda(typed_lambda_impl)  # str -> int

    assert typed_lambda.get_input_jsonschema() == {
        "title": "typed_lambda_impl_input",
        "type": "string",
    }
    assert typed_lambda.get_output_jsonschema() == {
        "title": "typed_lambda_impl_output",
        "type": "integer",
    }

    async def typed_async_lambda_impl(x: str) -> int:
        return len(x)

    typed_async_lambda = RunnableLambda(typed_async_lambda_impl)  # str -> int

    assert typed_async_lambda.get_input_jsonschema() == {
        "title": "typed_async_lambda_impl_input",
        "type": "string",
    }
    assert typed_async_lambda.get_output_jsonschema() == {
        "title": "typed_async_lambda_impl_output",
        "type": "integer",
    }

    fake_ret = FakeRetriever()  # str -> list[Document]

    assert fake_ret.get_input_jsonschema() == {
        "title": "FakeRetrieverInput",
        "type": "string",
    }
    assert _normalize_schema(fake_ret.get_output_jsonschema()) == {
        "$defs": {
            "Document": {
                "description": "Class for storing a piece of text and "
                "associated metadata.\n"
                "\n"
                "!!! note\n"
                "\n"
                "    `Document` is for **retrieval workflows**, not chat I/O. For "
                "sending text\n"
                "    to an LLM in a conversation, use message types from "
                "`langchain.messages`.\n"
                "\n"
                "Example:\n"
                "    ```python\n"
                "    from langchain_core.documents import Document\n"
                "\n"
                "    document = Document(\n"
                '        page_content="Hello, world!", '
                'metadata={"source": "https://example.com"}\n'
                "    )\n"
                "    ```",
                "properties": {
                    "id": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "default": None,
                        "title": "Id",
                    },
                    "metadata": {"title": "Metadata", "type": "object"},
                    "page_content": {"title": "Page Content", "type": "string"},
                    "type": {
                        "const": "Document",
                        "default": "Document",
                        "title": "Type",
                    },
                },
                "required": ["page_content"],
                "title": "Document",
                "type": "object",
            }
        },
        "items": {"$ref": "#/$defs/Document"},
        "title": "FakeRetrieverOutput",
        "type": "array",
    }

    fake_llm = FakeListLLM(responses=["a"])  # str -> list[list[str]]

    assert _schema(fake_llm.input_schema) == snapshot(name="fake_llm_input_schema")
    assert _schema(fake_llm.output_schema) == {
        "title": "FakeListLLMOutput",
        "type": "string",
    }

    fake_chat = FakeListChatModel(responses=["a"])  # str -> list[list[str]]

    assert _schema(fake_chat.input_schema) == snapshot(name="fake_chat_input_schema")
    assert _schema(fake_chat.output_schema) == snapshot(name="fake_chat_output_schema")

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="history"),
            ("human", "Hello, how are you?"),
        ]
    )

    assert _normalize_schema(chat_prompt.get_input_jsonschema()) == snapshot(
        name="chat_prompt_input_schema"
    )
    assert _normalize_schema(chat_prompt.get_output_jsonschema()) == snapshot(
        name="chat_prompt_output_schema"
    )

    prompt = PromptTemplate.from_template("Hello, {name}!")

    assert prompt.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {"name": {"title": "Name", "type": "string"}},
        "required": ["name"],
    }
    assert _schema(prompt.output_schema) == snapshot(name="prompt_output_schema")

    prompt_mapper = PromptTemplate.from_template("Hello, {name}!").map()

    assert _normalize_schema(prompt_mapper.get_input_jsonschema()) == {
        "$defs": {
            "PromptInput": {
                "properties": {"name": {"title": "Name", "type": "string"}},
                "required": ["name"],
                "title": "PromptInput",
                "type": "object",
            }
        },
        "default": None,
        "items": {"$ref": "#/$defs/PromptInput"},
        "title": "RunnableEach<PromptTemplate>Input",
        "type": "array",
    }
    assert _schema(prompt_mapper.output_schema) == snapshot(
        name="prompt_mapper_output_schema"
    )

    list_parser = CommaSeparatedListOutputParser()

    assert _schema(list_parser.input_schema) == snapshot(
        name="list_parser_input_schema"
    )
    assert _schema(list_parser.output_schema) == {
        "title": "CommaSeparatedListOutputParserOutput",
        "type": "array",
        "items": {"type": "string"},
    }

    seq = prompt | fake_llm | list_parser

    assert seq.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {"name": {"title": "Name", "type": "string"}},
        "required": ["name"],
    }
    assert seq.get_output_jsonschema() == {
        "type": "array",
        "items": {"type": "string"},
        "title": "CommaSeparatedListOutputParserOutput",
    }

    router: Runnable = RouterRunnable({})

    assert _schema(router.input_schema) == {
        "$ref": "#/definitions/RouterInput",
        "definitions": {
            "RouterInput": {
                "description": "Router input.",
                "properties": {
                    "input": {"title": "Input"},
                    "key": {"title": "Key", "type": "string"},
                },
                "required": ["key", "input"],
                "title": "RouterInput",
                "type": "object",
            }
        },
        "title": "RouterRunnableInput",
    }
    assert router.get_output_jsonschema() == {"title": "RouterRunnableOutput"}

    seq_w_map: Runnable = (
        prompt
        | fake_llm
        | {
            "original": RunnablePassthrough(input_type=str),
            "as_list": list_parser,
            "length": typed_lambda_impl,
        }
    )

    assert seq_w_map.get_input_jsonschema() == {
        "title": "PromptInput",
        "type": "object",
        "properties": {"name": {"title": "Name", "type": "string"}},
        "required": ["name"],
    }
    assert seq_w_map.get_output_jsonschema() == {
        "title": "RunnableParallel<original,as_list,length>Output",
        "type": "object",
        "properties": {
            "original": {"title": "Original", "type": "string"},
            "length": {"title": "Length", "type": "integer"},
            "as_list": {
                "title": "As List",
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["original", "as_list", "length"],
    }

    # Add a test for schema of runnable assign
    def foo(x: int) -> int:
        return x

    foo_ = RunnableLambda(foo)

    assert foo_.assign(bar=lambda _: "foo").get_output_schema().model_json_schema() == {
        "properties": {"bar": {"title": "Bar"}, "root": {"title": "Root"}},
        "required": ["root", "bar"],
        "title": "RunnableAssignOutput",
        "type": "object",
    }