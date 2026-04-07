def accepted_type(self, media_type):
        """
        Return the MediaType instance which best matches the given media type.
        """
        media_type = MediaType(media_type)
        return next(
            (
                accepted_type
                for accepted_type in self.accepted_types_by_precedence
                if media_type.match(accepted_type)
            ),
            None,
        )