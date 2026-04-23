def results(
    request: pytest.FixtureRequest, tz_info: dt.tzinfo, language: str
) -> Iterable:
    """Return localized results."""
    if not hasattr(request, "param"):
        return None

    # If results are generated, by using the HDate library, we need to set the language
    set_language(language)

    if isinstance(request.param, dict):
        result = {
            key: value.replace(tzinfo=tz_info)
            if isinstance(value, dt.datetime)
            else value
            for key, value in request.param.items()
        }
        if "attr" in result and isinstance(result["attr"], dict):
            result["attr"] = {
                key: value() if callable(value) else value
                for key, value in result["attr"].items()
            }
        return result
    return request.param