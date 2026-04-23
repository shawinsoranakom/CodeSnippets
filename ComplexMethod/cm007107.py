async def _save_message(self, message: Message, path: Path, fmt: str) -> str:
        """Save a Message to the specified file format, handling async iterators."""
        content = ""
        if message.text is None:
            content = ""
        elif isinstance(message.text, AsyncIterator):
            async for item in message.text:
                content += str(item) + " "
            content = content.strip()
        elif isinstance(message.text, Iterator):
            content = " ".join(str(item) for item in message.text)
        else:
            content = str(message.text)

        append_mode = getattr(self, "append_mode", False)
        should_append = append_mode and path.exists() and self._is_plain_text_format(fmt)

        if fmt == "txt":
            if should_append:
                path.write_text(path.read_text(encoding="utf-8") + "\n" + content, encoding="utf-8")
            else:
                path.write_text(content, encoding="utf-8")
        elif fmt == "json":
            new_message = {"message": content}
            if should_append:
                # Read and parse existing JSON
                existing_data = []
                try:
                    existing_content = path.read_text(encoding="utf-8").strip()
                    if existing_content:
                        parsed = json.loads(existing_content)
                        # Handle case where existing content is a single object
                        if isinstance(parsed, dict):
                            existing_data = [parsed]
                        elif isinstance(parsed, list):
                            existing_data = parsed
                except (json.JSONDecodeError, FileNotFoundError):
                    # Treat parse errors or missing file as empty array
                    existing_data = []

                # Append new message
                existing_data.append(new_message)

                # Write back as a single JSON array
                path.write_text(json.dumps(existing_data, indent=2), encoding="utf-8")
            else:
                path.write_text(json.dumps(new_message, indent=2), encoding="utf-8")
        elif fmt == "markdown":
            md_content = f"**Message:**\n\n{content}"
            if should_append:
                path.write_text(path.read_text(encoding="utf-8") + "\n\n" + md_content, encoding="utf-8")
            else:
                path.write_text(md_content, encoding="utf-8")
        else:
            msg = f"Unsupported Message format: {fmt}"
            raise ValueError(msg)
        action = "appended to" if should_append else "saved successfully as"
        return f"Message {action} '{path}'"