def set_annotation_mask(self, names):
        """Set the mask of annotations that will be returned by the SELECT."""
        if names is None:
            self.annotation_select_mask = None
        else:
            self.annotation_select_mask = set(names)
            if self.selected:
                # Prune the masked annotations.
                self.selected = {
                    key: value
                    for key, value in self.selected.items()
                    if not isinstance(value, str)
                    or value in self.annotation_select_mask
                }
                # Append the unmasked annotations.
                for name in names:
                    self.selected[name] = name
        self._annotation_select_cache = None