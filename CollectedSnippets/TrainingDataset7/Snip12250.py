def add_annotation(self, annotation, alias, select=True):
        """Add a single annotation expression to the Query."""
        self.check_alias(alias)
        annotation = annotation.resolve_expression(self, allow_joins=True, reuse=None)
        if select:
            self.append_annotation_mask([alias])
        else:
            self.set_annotation_mask(set(self.annotation_select).difference({alias}))
        self.annotations[alias] = annotation
        if select and self.selected:
            self.selected[alias] = alias