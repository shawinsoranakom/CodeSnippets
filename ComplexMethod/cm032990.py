def filter_channels(
    all_channels: list[ChannelType],
    channels_to_connect: list[str] | None,
    regex_enabled: bool,
) -> list[ChannelType]:
    if not channels_to_connect:
        return all_channels

    if regex_enabled:
        return [
            channel
            for channel in all_channels
            if any(
                re.fullmatch(channel_to_connect, channel["name"])
                for channel_to_connect in channels_to_connect
            )
        ]

    # Validate all specified channels are valid
    all_channel_names = {channel["name"] for channel in all_channels}
    for channel in channels_to_connect:
        if channel not in all_channel_names:
            raise ValueError(
                f"Channel '{channel}' not found in workspace. "
                f"Available channels (Showing {len(all_channel_names)} of "
                f"{min(len(all_channel_names), MAX_CHANNELS_TO_LOG)}): "
                f"{list(itertools.islice(all_channel_names, MAX_CHANNELS_TO_LOG))}"
            )

    return [
        channel for channel in all_channels if channel["name"] in channels_to_connect
    ]