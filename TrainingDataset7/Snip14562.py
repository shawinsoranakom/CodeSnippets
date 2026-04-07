def format_subject(self, subject):
        """
        Escape CR and LF characters.
        """
        return subject.replace("\n", "\\n").replace("\r", "\\r")