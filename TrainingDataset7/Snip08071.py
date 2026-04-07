def items(self):
        # Make sure to return a clone; we don't want premature evaluation.
        return self.queryset.filter()