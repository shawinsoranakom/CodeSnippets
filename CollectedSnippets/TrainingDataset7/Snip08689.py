def body_contains(self, text):
        """
        Checks that ``text`` occurs in the email body and in all attached MIME
        type text/* alternatives.
        """
        if text not in self.body:
            return False

        for content, mimetype in self.alternatives:
            if mimetype.startswith("text/") and text not in content:
                return False
        return True