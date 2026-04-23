def attach_file(self, msg: Message, item: dict, kind: str = ATTR_FILE_KIND_FILE):
        """Append a file or image to message."""
        file_name = None
        mime_type = None

        if ATTR_FILE_NAME in item:
            file_name = item[ATTR_FILE_NAME]

        if ATTR_FILE_MIME_TYPE in item:
            mime_type = item[ATTR_FILE_MIME_TYPE]

        if ATTR_FILE_URL in item:
            if kind == ATTR_FILE_KIND_IMAGE:
                msg.add_image_from_url(item[ATTR_FILE_URL], file_name, mime_type)
            else:
                msg.add_file_from_url(item[ATTR_FILE_URL], file_name, mime_type)
        elif ATTR_FILE_CONTENT in item:
            if kind == ATTR_FILE_KIND_IMAGE:
                msg.add_image_from_content(
                    item[ATTR_FILE_CONTENT], file_name, mime_type
                )
            else:
                msg.add_file_from_content(item[ATTR_FILE_CONTENT], file_name, mime_type)
        elif ATTR_FILE_PATH in item:
            file_exists = self.file_exists(item[ATTR_FILE_PATH])

            if file_exists:
                if kind == ATTR_FILE_KIND_IMAGE:
                    msg.add_image(item[ATTR_FILE_PATH], file_name, mime_type)
                else:
                    msg.add_file(item[ATTR_FILE_PATH], file_name, mime_type)
            else:
                _LOGGER.error("File does not exist: %s", item[ATTR_FILE_PATH])