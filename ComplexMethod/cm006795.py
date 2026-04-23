def load_files_message(self) -> Message:
        """Load files and return as Message.

        Returns:
          Message: Message containing all file data
        """
        data_list = self.load_files_core()
        if not data_list:
            return Message()

        # Extract metadata from the first data item
        metadata = self._extract_file_metadata(data_list[0])

        sep: str = getattr(self, "separator", "\n\n") or "\n\n"
        parts: list[str] = []
        for d in data_list:
            try:
                data_text = self._extract_text(d)
                if data_text and isinstance(data_text, str):
                    parts.append(data_text)
                elif data_text:
                    # get_text() returned non-string, convert it
                    parts.append(str(data_text))
                elif isinstance(d.data, dict):
                    # convert the data dict to a readable string
                    parts.append(orjson.dumps(d.data, option=orjson.OPT_INDENT_2, default=str).decode())
                else:
                    parts.append(str(d))
            except Exception:  # noqa: BLE001
                # Final fallback - just try to convert to string
                # TODO: Consider downstream error case more. Should this raise an error?
                parts.append(str(d))

        return Message(text=sep.join(parts), **metadata)