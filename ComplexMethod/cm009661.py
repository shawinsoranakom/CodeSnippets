def test_docstring_parsing() -> None:
    expected = {
        "title": "foo",
        "description": "The foo.",
        "type": "object",
        "properties": {
            "bar": {"title": "Bar", "description": "The bar.", "type": "string"},
            "baz": {"title": "Baz", "description": "The baz.", "type": "integer"},
        },
        "required": ["bar", "baz"],
    }

    # Simple case
    def foo(bar: str, baz: int) -> str:
        """The foo.

        Args:
            bar: The bar.
            baz: The baz.
        """
        return bar

    as_tool = tool(foo, parse_docstring=True)
    args_schema = _schema(as_tool.args_schema)
    assert args_schema["description"] == "The foo."
    assert args_schema["properties"] == expected["properties"]

    # Multi-line description
    def foo2(bar: str, baz: int) -> str:
        """The foo.

        Additional description here.

        Args:
            bar: The bar.
            baz: The baz.
        """
        return bar

    as_tool = tool(foo2, parse_docstring=True)
    args_schema2 = _schema(as_tool.args_schema)
    assert args_schema2["description"] == "The foo. Additional description here."
    assert args_schema2["properties"] == expected["properties"]

    # Multi-line with Returns block
    def foo3(bar: str, baz: int) -> str:
        """The foo.

        Additional description here.

        Args:
            bar: The bar.
            baz: The baz.

        Returns:
            description of returned value.
        """
        return bar

    as_tool = tool(foo3, parse_docstring=True)
    args_schema3 = _schema(as_tool.args_schema)
    args_schema3["title"] = "foo2"
    assert args_schema2 == args_schema3

    # Single argument
    def foo4(bar: str) -> str:
        """The foo.

        Args:
            bar: The bar.
        """
        return bar

    as_tool = tool(foo4, parse_docstring=True)
    args_schema4 = _schema(as_tool.args_schema)
    assert args_schema4["description"] == "The foo."
    assert args_schema4["properties"] == {
        "bar": {"description": "The bar.", "title": "Bar", "type": "string"}
    }