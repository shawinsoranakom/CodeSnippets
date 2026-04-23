async def on_ready():
            # Try to parse as channel ID first
            channel = None
            try:
                channel_id = int(channel_identifier)
                channel = client.get_channel(channel_id)
                if channel:
                    result["channel_id"] = str(channel.id)
                    # Private channels may not have a name attribute
                    result["channel_name"] = getattr(channel, "name", "Private Channel")
                    # Check if channel has guild (not private)
                    if hasattr(channel, "guild"):
                        guild = getattr(channel, "guild", None)
                        if guild:
                            result["server_id"] = str(guild.id)
                            result["server_name"] = guild.name
                        else:
                            result["server_id"] = ""
                            result["server_name"] = "Direct Message"
                    else:
                        result["server_id"] = ""
                        result["server_name"] = "Direct Message"
                    # Get channel type safely
                    result["channel_type"] = str(getattr(channel, "type", "unknown"))
                    await client.close()
                    return
            except ValueError:
                # Not an ID, treat as channel name
                for guild in client.guilds:
                    if server_name and guild.name != server_name:
                        continue
                    for ch in guild.channels:
                        if ch.name == channel_identifier:
                            result["channel_id"] = str(ch.id)
                            result["channel_name"] = ch.name
                            result["server_id"] = str(guild.id)
                            result["server_name"] = guild.name
                            result["channel_type"] = str(ch.type)
                            await client.close()
                            return

            result["error"] = f"Channel not found: {channel_identifier}"
            await client.close()