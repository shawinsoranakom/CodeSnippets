async def on_ready():
            print(f"Logged in as {client.user}")
            channel = None

            # Try to parse as channel ID first
            try:
                channel_id = int(channel_name)
                channel = client.get_channel(channel_id)
            except ValueError:
                # Not a valid ID, will try name lookup
                pass

            # If not found by ID (or not an ID), try name lookup
            if not channel:
                for guild in client.guilds:
                    if server_name and guild.name != server_name:
                        continue
                    for ch in guild.text_channels:
                        if ch.name == channel_name:
                            channel = ch
                            break
                    if channel:
                        break

            if not channel:
                result["status"] = f"Channel not found: {channel_name}"
                await client.close()
                return

            # Type check - ensure it's a text channel that can send messages
            if not hasattr(channel, "send"):
                result["status"] = (
                    f"Channel {channel_name} cannot receive messages (not a text channel)"
                )
                await client.close()
                return

            # Split message into chunks if it exceeds 2000 characters
            chunks = self.chunk_message(message_content)
            last_message = None
            for chunk in chunks:
                last_message = await channel.send(chunk)  # type: ignore
            result["status"] = "Message sent"
            result["message_id"] = str(last_message.id) if last_message else ""
            result["channel_id"] = str(channel.id)
            await client.close()