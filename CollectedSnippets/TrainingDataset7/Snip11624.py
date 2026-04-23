def identity(self):
        return (
            *super().identity,
            self.through,
            make_hashable(self.through_fields),
            self.db_constraint,
        )