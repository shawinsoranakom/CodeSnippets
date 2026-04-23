def _serialize_platform_types(data: Any) -> Any:
    """Recursively convert PlatformType enums to strings in dicts and sets."""
    if isinstance(data, dict):
        return {
            (
                platform.value if isinstance(platform, PlatformType) else platform
            ): _serialize_platform_types(record)
            for platform, record in data.items()
        }
    if isinstance(data, set):
        return sorted(
            [
                record.value if isinstance(record, PlatformType) else record
                for record in data
            ]
        )
    if isinstance(data, PlatformType):
        return data.value
    return data