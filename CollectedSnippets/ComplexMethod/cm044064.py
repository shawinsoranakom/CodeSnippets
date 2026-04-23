def test_omni_widget_response_model():
    # Create a sample OmniWidgetResponseModel instance

    test_table = [
        {"symbol": "AAPL", "price": 150.0, "volume": 1000000},
        {"symbol": "GOOGL", "price": 2800.0, "volume": 500000},
    ]
    widget = OmniWidgetResponseModel(
        content=test_table,
    )
    # Assert the content and data_format fields
    assert widget.content == test_table
    assert widget.data_format == {
        "data_type": "object",
        "parse_as": "table",
    }
    assert not hasattr(widget, "parse_as")

    widget = OmniWidgetResponseModel(
        content=test_table,
        parse_as="text",
    )
    # Assert the parse_as field takes precedence
    assert widget.content == test_table
    assert widget.data_format == {
        "data_type": "object",
        "parse_as": "text",
    }
    # Assert that the parse_as field is not sent at the root of the object.
    assert not hasattr(widget, "parse_as")

    # Test with JSON string content
    widget = OmniWidgetResponseModel(
        content=json.dumps(test_table),
    )

    # Assert the content and data_format fields
    assert isinstance(widget.content, list)
    assert widget.data_format == {
        "data_type": "object",
        "parse_as": "table",
    }
    assert not hasattr(widget, "parse_as")

    assert "x-widget_config" in widget.schema_json()