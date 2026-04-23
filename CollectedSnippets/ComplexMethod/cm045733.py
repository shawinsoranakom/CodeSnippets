def mock_get_text_embedding(text: str) -> List[float]:
    """Mock get text embedding."""
    if text == "Hello world.":
        return [1.0, 0.0, 0.0, 0.0, 0.0]
    elif text == "This is a test.":
        return [0.0, 1.0, 0.0, 0.0, 0.0]
    elif text == "This is another test.":
        return [0.0, 0.0, 1.0, 0.0, 0.0]
    elif text == "This is a test v2.":
        return [0.0, 0.0, 0.0, 1.0, 0.0]
    elif text == "This is a test v3.":
        return [0.0, 0.0, 0.0, 0.0, 1.0]
    elif text == "This is bar test.":
        return [0.0, 0.0, 1.0, 0.0, 0.0]
    elif text == "Hello world backup.":
        return [0.0, 0.0, 0.0, 0.0, 1.0]
    else:
        return [0.0, 0.0, 0.0, 0.0, 0.0]