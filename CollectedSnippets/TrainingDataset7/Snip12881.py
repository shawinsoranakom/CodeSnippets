def accepts(self, media_type):
        """Does the client accept a response in the given media type?"""
        return self.accepted_type(media_type) is not None