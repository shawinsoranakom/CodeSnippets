def parse_media_source_id(
    media_source_id: str,
) -> ParsedMediaSourceId | ParsedMediaSourceStreamId:
    """Turn a media source ID into options."""
    parsed = URL(media_source_id)

    if parsed.path.startswith(f"{MEDIA_SOURCE_STREAM_PATH}/"):
        return {"stream": parsed.path[len(MEDIA_SOURCE_STREAM_PATH) + 1 :]}

    if URL_QUERY_TTS_OPTIONS in parsed.query:
        try:
            options = json.loads(parsed.query[URL_QUERY_TTS_OPTIONS])
        except json.JSONDecodeError as err:
            raise Unresolvable(f"Invalid TTS options: {err.msg}") from err
    else:
        options = {
            k: v
            for k, v in parsed.query.items()
            if k not in ("message", "language", "cache")
        }
    if "message" not in parsed.query:
        raise Unresolvable("No message specified.")
    kwargs: MediaSourceOptions = {
        "engine": parsed.name,
        "language": parsed.query.get("language"),
        "options": options,
        "use_file_cache": None,
    }
    if "cache" in parsed.query:
        kwargs["use_file_cache"] = parsed.query["cache"] == "true"

    return {"message": parsed.query["message"], "options": kwargs}