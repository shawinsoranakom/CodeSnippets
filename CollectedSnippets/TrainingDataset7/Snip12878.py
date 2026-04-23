def accepted_types_by_precedence(self):
        """
        Return a list of MediaType instances, in order of precedence
        (specificity).
        """
        return sorted(
            self.accepted_types,
            key=operator.attrgetter("specificity", "quality"),
            reverse=True,
        )