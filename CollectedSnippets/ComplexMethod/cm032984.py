async def _fetch_filtered_channels(
    discord_client: Client,
    server_ids: list[int] | None,
    channel_names: list[str] | None,
) -> list[TextChannel]:
    filtered_channels: list[TextChannel] = []

    for channel in discord_client.get_all_channels():
        if not channel.permissions_for(channel.guild.me).read_message_history:
            continue
        if not isinstance(channel, TextChannel):
            continue
        if server_ids and len(server_ids) > 0 and channel.guild.id not in server_ids:
            continue
        if channel_names and channel.name not in channel_names:
            continue
        filtered_channels.append(channel)

    logging.info(f"Found {len(filtered_channels)} channels for the authenticated user")
    return filtered_channels