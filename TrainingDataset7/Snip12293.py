def set_group_by(self, allow_aliases=True):
        """
        Expand the GROUP BY clause required by the query.

        This will usually be the set of all non-aggregate fields in the
        return data. If the database backend supports grouping by the
        primary key, and the query would be equivalent, the optimization
        will be made automatically.
        """
        if allow_aliases and self.values_select:
            # If grouping by aliases is allowed assign selected value aliases
            # by moving them to annotations.
            group_by_annotations = {}
            values_select = {}
            for alias, expr in zip(self.values_select, self.select):
                if isinstance(expr, Col):
                    values_select[alias] = expr
                else:
                    group_by_annotations[alias] = expr
            self.annotations = {**group_by_annotations, **self.annotations}
            self.append_annotation_mask(group_by_annotations)
            self.select = tuple(values_select.values())
            self.values_select = tuple(values_select)
            if self.selected is not None:
                for index, value_select in enumerate(values_select):
                    self.selected[value_select] = index
        group_by = list(self.select)
        for alias, annotation in self.annotation_select.items():
            if not (group_by_cols := annotation.get_group_by_cols()):
                continue
            if allow_aliases and not annotation.contains_aggregate:
                group_by.append(Ref(alias, annotation))
            else:
                group_by.extend(group_by_cols)
        self.group_by = tuple(group_by)