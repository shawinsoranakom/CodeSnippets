def __hash__(self):
        if hasattr(self, "message"):
            return hash(
                (
                    self.message,
                    self.code,
                    make_hashable(self.params),
                )
            )
        if hasattr(self, "error_dict"):
            return hash(make_hashable(self.error_dict))
        return hash(tuple(sorted(self.error_list, key=operator.attrgetter("message"))))