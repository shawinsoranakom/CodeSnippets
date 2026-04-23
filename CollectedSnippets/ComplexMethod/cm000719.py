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

            try:
                # Handle MediaFileType - could be data URI, URL, or local path
                file_bytes = None
                detected_filename = filename

                if file.startswith("data:"):
                    # Data URI - extract the base64 content
                    header, encoded = file.split(",", 1)
                    file_bytes = base64.b64decode(encoded)

                    # Try to get MIME type and suggest filename if not provided
                    if not filename and ";" in header:
                        mime_match = header.split(":")[1].split(";")[0]
                        ext = mimetypes.guess_extension(mime_match) or ".bin"
                        detected_filename = f"file{ext}"

                elif file.startswith(("http://", "https://")):
                    # URL - download the file
                    response = await Requests().get(file)
                    file_bytes = response.content

                    # Try to get filename from URL if not provided
                    if not filename:
                        from urllib.parse import urlparse

                        path = urlparse(file).path
                        detected_filename = Path(path).name or "download"
                else:
                    # Local file path - read from stored media file
                    # This would be a path from a previous block's output
                    stored_file = await store_media_file(
                        file=file,
                        execution_context=execution_context,
                        return_format="for_external_api",  # Get content to send to Discord
                    )
                    # Now process as data URI
                    header, encoded = stored_file.split(",", 1)
                    file_bytes = base64.b64decode(encoded)

                    if not filename:
                        detected_filename = Path(file).name or "file"

                if not file_bytes:
                    result["status"] = "Error: Could not read file content"
                    await client.close()
                    return

                # Create Discord file object
                discord_file = discord.File(
                    io.BytesIO(file_bytes), filename=detected_filename or "file"
                )

                # Type check - ensure it's a text channel that can send messages
                if not hasattr(channel, "send"):
                    result["status"] = (
                        f"Channel {channel_identifier} cannot receive messages (not a text channel)"
                    )
                    await client.close()
                    return

                # Send the file
                message = await channel.send(  # type: ignore
                    content=message_content if message_content else None,
                    file=discord_file,
                )
                result["status"] = "File sent successfully"
                result["message_id"] = str(message.id)
            except Exception as e:
                result["status"] = f"Error sending file: {str(e)}"
            finally:
                await client.close()