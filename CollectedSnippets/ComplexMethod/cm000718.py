async def on_ready():
            channel = None

            # Try to parse as channel ID first
            try:
                channel_id = int(channel_identifier)
                channel = client.get_channel(channel_id)
            except ValueError:
                # Not an ID, treat as channel name
                for guild in client.guilds:
                    if server_name and guild.name != server_name:
                        continue
                    for ch in guild.text_channels:
                        if ch.name == channel_identifier:
                            channel = ch
                            break
                    if channel:
                        break

            if not channel:
                result["status"] = f"Channel not found: {channel_identifier}"
                await client.close()
                return

            # Build the embed
            embed = discord.Embed(
                title=embed_data.get("title") or None,
                description=embed_data.get("description") or None,
                color=embed_data.get("color", 0x5865F2),
            )

            if embed_data.get("thumbnail_url"):
                embed.set_thumbnail(url=embed_data["thumbnail_url"])

            if embed_data.get("image_url"):
                embed.set_image(url=embed_data["image_url"])

            if embed_data.get("author_name"):
                embed.set_author(name=embed_data["author_name"])

            if embed_data.get("footer_text"):
                embed.set_footer(text=embed_data["footer_text"])

            # Add fields
            for field in embed_data.get("fields", []):
                if isinstance(field, dict) and "name" in field and "value" in field:
                    embed.add_field(
                        name=field["name"],
                        value=field["value"],
                        inline=field.get("inline", True),
                    )

            try:
                # Type check - ensure it's a text channel that can send messages
                if not hasattr(channel, "send"):
                    result["status"] = (
                        f"Channel {channel_identifier} cannot receive messages (not a text channel)"
                    )
                    await client.close()
                    return

                message = await channel.send(embed=embed)  # type: ignore
                result["status"] = "Embed sent successfully"
                result["message_id"] = str(message.id)
            except Exception as e:
                result["status"] = f"Error sending embed: {str(e)}"
            finally:
                await client.close()