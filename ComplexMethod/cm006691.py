def get_file_content_dicts(self, model_name: str | None = None):
        def _safe_attachment_name(value: Any) -> str | None:
            if isinstance(value, Image):
                if not value.path:
                    return None
                try:
                    return Path(value.path).name
                except (OSError, TypeError, ValueError):
                    return None
            try:
                return Path(value).name
            except (OSError, TypeError, ValueError):
                return None

        content_dicts = []
        try:
            files = get_file_paths(self.files)
        except (OSError, TypeError, ValueError) as exc:
            logger.error(
                "Error getting file paths",
                error_type=type(exc).__name__,
                exc_info=True,
            )
            return content_dicts

        for file in files:
            if isinstance(file, Image):
                content_dicts.append(file.to_content_dict(flow_id=self.flow_id))
                continue

            try:
                if is_image_file(file):
                    content_dicts.append(create_image_content_dict(file, None, model_name))
                    continue

                try:
                    file_size_bytes = Path(file).stat().st_size
                except (OSError, ValueError) as exc:
                    logger.warning(
                        "Skipping attachment during message conversion: could not stat file",
                        error_type=type(exc).__name__,
                        file_name=_safe_attachment_name(file),
                    )
                    continue

                if file_size_bytes > MAX_ATTACHMENT_SIZE_BYTES:
                    continue

                from lfx.base.data.utils import parse_text_file_to_data

                parsed_file = parse_text_file_to_data(file, silent_errors=True)
                parsed_data = parsed_file.data if parsed_file else {}
                parsed_text = parsed_data.get("text") if isinstance(parsed_data, dict) else None
                if not parsed_text:
                    continue

                parsed_text_str = parsed_text if isinstance(parsed_text, str) else json.dumps(parsed_text)
                file_name = _safe_attachment_name(file) or "attachment"
                content_dicts.append(
                    {
                        "type": "text",
                        "text": f"Attachment: {file_name}\n{parsed_text_str}",
                    }
                )
            except PermissionError as exc:
                logger.error(
                    "Skipping attachment during message conversion: permission denied",
                    error_type=type(exc).__name__,
                    file_name=_safe_attachment_name(file),
                    exc_info=True,
                )
                continue
            except (FileNotFoundError, UnicodeDecodeError, ValueError, OSError) as exc:
                logger.warning(
                    "Skipping unsupported attachment during message conversion",
                    error_type=type(exc).__name__,
                    file_name=_safe_attachment_name(file),
                )
                continue
        return content_dicts