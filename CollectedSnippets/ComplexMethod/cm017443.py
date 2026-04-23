def set_values(self, fields):
        self.select_related = False
        self.clear_deferred_loading()
        self.clear_select_fields()

        selected = {}
        if fields:
            for field in fields:
                self.check_alias(field)
            field_names = []
            extra_names = []
            annotation_names = []
            if not self.extra and not self.annotations:
                # Shortcut - if there are no extra or annotations, then
                # the values() clause must be just field names.
                field_names = list(fields)
                selected = dict(zip(fields, range(len(fields))))
            else:
                self.default_cols = False
                for f in fields:
                    if extra := self.extra_select.get(f):
                        extra_names.append(f)
                        selected[f] = RawSQL(*extra)
                    elif f in self.annotation_select:
                        annotation_names.append(f)
                        selected[f] = f
                    elif f in self.annotations:
                        if self.annotation_select:
                            raise FieldError(
                                f"Cannot select the '{f}' alias. It was excluded "
                                f"by a previous values() or values_list() call. "
                                f"Include '{f}' in that call to select it."
                            )
                        else:
                            raise FieldError(
                                f"Cannot select the '{f}' alias. Use annotate() "
                                f"to promote it."
                            )
                    else:
                        # Call `names_to_path` to ensure a FieldError including
                        # annotations about to be masked as valid choices if
                        # `f` is not resolvable.
                        if self.annotation_select:
                            self.names_to_path(f.split(LOOKUP_SEP), self.model._meta)
                        selected[f] = len(field_names)
                        field_names.append(f)
            self.set_extra_mask(extra_names)
            self.set_annotation_mask(annotation_names)
        else:
            field_names = [f.attname for f in self.model._meta.concrete_fields]
            selected = dict.fromkeys(field_names, None)
        # Selected annotations must be known before setting the GROUP BY
        # clause.
        if self.group_by is True:
            self.add_fields(
                (f.attname for f in self.model._meta.concrete_fields), False
            )
            # Disable GROUP BY aliases to avoid orphaning references to the
            # SELECT clause which is about to be cleared.
            self.set_group_by(allow_aliases=False)
            self.clear_select_fields()
        elif self.group_by:
            # Resolve GROUP BY annotation references if they are not part of
            # the selected fields anymore.
            group_by = []
            for expr in self.group_by:
                if isinstance(expr, Ref) and expr.refs not in selected:
                    expr = self.annotations[expr.refs]
                group_by.append(expr)
            self.group_by = tuple(group_by)

        self.values_select = tuple(field_names)
        self.add_fields(field_names, True)
        self.selected = selected if fields else None