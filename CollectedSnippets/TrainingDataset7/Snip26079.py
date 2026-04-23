def get_message_structure(self, message, level=0):
        """
        Return a multiline indented string representation
        of the message's MIME content-type structure, e.g.:

            multipart/mixed
                multipart/alternative
                    text/plain
                    text/html
                image/jpg
                text/calendar
        """
        # Adapted from email.iterators._structure().
        indent = " " * (level * 4)
        structure = [f"{indent}{message.get_content_type()}\n"]
        if message.is_multipart():
            for subpart in message.get_payload():
                structure.append(self.get_message_structure(subpart, level + 1))
        return "".join(structure)