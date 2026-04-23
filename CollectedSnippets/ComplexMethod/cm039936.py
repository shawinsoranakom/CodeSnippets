def check_warnings_as_errors(warning_info, warnings_as_errors):
    if warning_info.action == "error" and warnings_as_errors:
        with pytest.raises(warning_info.category, match=warning_info.message):
            warnings.warn(
                message=warning_info.message,
                category=warning_info.category,
            )
    if warning_info.action == "ignore":
        with warnings.catch_warnings(record=True) as record:
            message = warning_info.message
            # Special treatment when regex is used
            if "Pyarrow" in message:
                message = "\nPyarrow will become a required dependency"
            # Regex in _testing.py; emit the real Python 3.14 deprecation text.
            elif message == r"codecs\.open\(\) is deprecated":
                message = "codecs.open() is deprecated. Use open() instead."

            warnings.warn(
                message=message,
                category=warning_info.category,
            )
            assert len(record) == 0 if warnings_as_errors else 1
            if record:
                assert str(record[0].message) == message
                assert record[0].category == warning_info.category