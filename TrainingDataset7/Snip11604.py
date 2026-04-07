def identity(self):
        return (
            self.field,
            self.model,
            self.related_name,
            self.related_query_name,
            make_hashable(self.limit_choices_to),
            self.parent_link,
            self.on_delete,
            self.symmetrical,
            self.multiple,
        )