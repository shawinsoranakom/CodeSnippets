def _format_message_content(self, message_content: MessageContent) -> str:
        """
        Formats the message content for logging.
        """
        # Start by converting the message content to a list of strings.
        content_list: List[str] = []
        content = message_content
        if isinstance(content, str):
            content_list.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    content_list.append(item.rstrip())
                elif isinstance(item, Image):
                    # Save the image to disk.
                    image_filename = str(self._get_next_page_id()) + " image.jpg"
                    image_path = os.path.join(self.log_dir, image_filename)
                    item.image.save(image_path)
                    # Add a link to the image.
                    content_list.append(self._link_to_image(image_filename, "message_image"))
                elif isinstance(item, Dict):
                    # Add a dictionary to the log.
                    json_str = json.dumps(item, indent=4)
                    content_list.append(json_str)
                else:
                    content_list.append(str(item).rstrip())
        else:
            content_list.append("<UNKNOWN MESSAGE CONTENT>")

        # Convert the list of strings to a single string containing newline separators.
        output = ""
        for item in content_list:
            output += f"\n{item}\n"
        return output