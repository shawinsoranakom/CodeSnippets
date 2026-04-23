def accepted_types(self):
        """
        Return a list of MediaType instances, in order of preference (quality).
        """
        header_value = self.headers.get("Accept", "*/*")
        return sorted(
            (
                media_type
                for token in header_value.split(",")
                if token.strip() and (media_type := MediaType(token)).quality != 0
            ),
            key=operator.attrgetter("quality", "specificity"),
            reverse=True,
        )