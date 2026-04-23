def get_preferred_type(self, media_types):
        """Select the preferred media type from the provided options."""
        if not media_types or not self.accepted_types:
            return None

        desired_types = [
            (accepted_type, media_type)
            for media_type in media_types
            if (accepted_type := self.accepted_type(media_type)) is not None
        ]

        if not desired_types:
            return None

        # Of the desired media types, select the one which is preferred.
        return min(desired_types, key=lambda t: self.accepted_types.index(t[0]))[1]