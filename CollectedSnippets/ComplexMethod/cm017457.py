def get_select_for_update_of_arguments(self):
        """
        Return a quoted list of arguments for the SELECT FOR UPDATE OF part of
        the query.
        """

        def _get_parent_klass_info(klass_info):
            concrete_model = klass_info["model"]._meta.concrete_model
            for parent_model, parent_link in concrete_model._meta.parents.items():
                all_parents = parent_model._meta.all_parents
                yield {
                    "model": parent_model,
                    "field": parent_link,
                    "reverse": False,
                    "select_fields": [
                        select_index
                        for select_index in klass_info["select_fields"]
                        # Selected columns from a model or its parents.
                        if (
                            self.select[select_index][0].target.model == parent_model
                            or self.select[select_index][0].target.model in all_parents
                        )
                    ],
                }

        def _get_first_selected_col_from_model(klass_info):
            """
            Find the first selected column from a model. If it doesn't exist,
            don't lock a model.

            select_fields is filled recursively, so it also contains fields
            from the parent models.
            """
            concrete_model = klass_info["model"]._meta.concrete_model
            for select_index in klass_info["select_fields"]:
                if self.select[select_index][0].target.model == concrete_model:
                    return self.select[select_index][0]

        def _get_field_choices():
            """Yield all allowed field paths in breadth-first search order."""
            queue = collections.deque([(None, self.klass_info)])
            while queue:
                parent_path, klass_info = queue.popleft()
                if parent_path is None:
                    path = []
                    yield "self"
                else:
                    field = klass_info["field"]
                    if klass_info["reverse"]:
                        field = field.remote_field
                    path = [*parent_path, field.name]
                    yield LOOKUP_SEP.join(path)
                queue.extend(
                    (path, klass_info)
                    for klass_info in _get_parent_klass_info(klass_info)
                )
                queue.extend(
                    (path, klass_info)
                    for klass_info in klass_info.get("related_klass_infos", [])
                )

        if not self.klass_info:
            return []
        result = []
        invalid_names = []
        for name in self.query.select_for_update_of:
            klass_info = self.klass_info
            if name == "self":
                col = _get_first_selected_col_from_model(klass_info)
            else:
                for part in name.split(LOOKUP_SEP):
                    klass_infos = (
                        *klass_info.get("related_klass_infos", []),
                        *_get_parent_klass_info(klass_info),
                    )
                    for related_klass_info in klass_infos:
                        field = related_klass_info["field"]
                        if related_klass_info["reverse"]:
                            field = field.remote_field
                        if field.name == part:
                            klass_info = related_klass_info
                            break
                    else:
                        klass_info = None
                        break
                if klass_info is None:
                    invalid_names.append(name)
                    continue
                col = _get_first_selected_col_from_model(klass_info)
            if col is not None:
                if self.connection.features.select_for_update_of_column:
                    result.append(self.compile(col)[0])
                else:
                    result.append(self.quote_name(col.alias))
        if invalid_names:
            raise FieldError(
                "Invalid field name(s) given in select_for_update(of=(...)): %s. "
                "Only relational fields followed in the query are allowed. "
                "Choices are: %s."
                % (
                    ", ".join(invalid_names),
                    ", ".join(_get_field_choices()),
                )
            )
        return result