async def on_ready():
            channel = None

            # Try to parse as channel ID first
            try:
                channel_id = int(channel_name)
                try:
                    channel = await client.fetch_channel(channel_id)
                except discord.errors.NotFound:
                    result["status"] = f"Channel with ID {channel_id} not found"
                    await client.close()
                    return
                except discord.errors.Forbidden:
                    result["status"] = (
                        f"Bot does not have permission to view channel {channel_id}"
                    )
                    await client.close()
                    return
            except ValueError:
                # Not an ID, treat as channel name
                # Collect all matching channels to detect duplicates
                matching_channels = []
                for guild in client.guilds:
                    # Skip guilds if server_name is provided and doesn't match
                    if (
                        server_name
                        and server_name.strip()
                        and guild.name != server_name
                    ):
                        continue
                    for ch in guild.text_channels:
                        if ch.name == channel_name:
                            matching_channels.append(ch)

                if not matching_channels:
                    result["status"] = f"Channel not found: {channel_name}"
                    await client.close()
                    return
                elif len(matching_channels) > 1:
                    result["status"] = (
                        f"Multiple channels named '{channel_name}' found. "
                        "Please specify server_name to disambiguate."
                    )
                    await client.close()
                    return
                else:
                    channel = matching_channels[0]

            if not channel:
                result["status"] = "Failed to resolve channel"
                await client.close()
                return

            # Type check - ensure it's a text channel that can create threads
            if not hasattr(channel, "create_thread"):
                result["status"] = (
                    f"Channel {channel_name} cannot create threads (not a text channel)"
                )
                await client.close()
                return

            # After the hasattr check, we know channel is a TextChannel
            channel = cast(discord.TextChannel, channel)

            try:
                # Create the thread using discord.py 2.0+ API
                thread_type = (
                    discord.ChannelType.private_thread
                    if is_private
                    else discord.ChannelType.public_thread
                )

                # Cast to the specific Literal type that discord.py expects
                duration_minutes = cast(
                    Literal[60, 1440, 4320, 10080], auto_archive_duration.to_minutes()
                )

                # The 'type' parameter exists in discord.py 2.0+ but isn't in type stubs yet
                # pyright: ignore[reportCallIssue]
                thread = await channel.create_thread(
                    name=thread_name,
                    type=thread_type,
                    auto_archive_duration=duration_minutes,
                )

                # Send initial message if provided
                if message_content:
                    await thread.send(message_content)

                result["status"] = "Thread created successfully"
                result["thread_id"] = str(thread.id)
                result["thread_name"] = thread.name

            except discord.errors.Forbidden as e:
                result["status"] = (
                    f"Bot does not have permission to create threads in this channel. {str(e)}"
                )
            except Exception as e:
                result["status"] = f"Error creating thread: {str(e)}"
            finally:
                await client.close()