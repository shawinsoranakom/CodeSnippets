def __getitem__(self, idx):
        # Prevent unnecessary reevaluation when accessing BoundField's attrs
        # from templates.
        if not isinstance(idx, (int, slice)):
            raise TypeError(
                "BoundField indices must be integers or slices, not %s."
                % type(idx).__name__
            )
        return self.subwidgets[idx]