def is_composite_pk(self):
        return isinstance(self.pk, CompositePrimaryKey)