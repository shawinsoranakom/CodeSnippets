def reduce(self, operation, app_label):
        if (
            isinstance(operation, DeleteModel)
            and self.name_lower == operation.name_lower
            and not self.options.get("proxy", False)
        ):
            return []
        elif (
            isinstance(operation, RenameModel)
            and self.name_lower == operation.old_name_lower
        ):
            return [replace(self, name=operation.new_name)]
        elif (
            isinstance(operation, AlterModelOptions)
            and self.name_lower == operation.name_lower
        ):
            options = {**self.options, **operation.options}
            for key in operation.ALTER_OPTION_KEYS:
                if key not in operation.options:
                    options.pop(key, None)
            return [replace(self, options=options)]
        elif (
            isinstance(operation, AlterModelManagers)
            and self.name_lower == operation.name_lower
        ):
            return [replace(self, managers=operation.managers)]
        elif (
            isinstance(operation, AlterModelTable)
            and self.name_lower == operation.name_lower
        ):
            return [
                replace(
                    self,
                    options={**self.options, "db_table": operation.table},
                ),
            ]
        elif (
            isinstance(operation, AlterModelTableComment)
            and self.name_lower == operation.name_lower
        ):
            return [
                replace(
                    self,
                    options={
                        **self.options,
                        "db_table_comment": operation.table_comment,
                    },
                ),
            ]
        elif (
            isinstance(operation, AlterTogetherOptionOperation)
            and self.name_lower == operation.name_lower
        ):
            return [
                replace(
                    self,
                    options={
                        **self.options,
                        **{operation.option_name: operation.option_value},
                    },
                ),
            ]
        elif (
            isinstance(operation, AlterOrderWithRespectTo)
            and self.name_lower == operation.name_lower
        ):
            return [
                replace(
                    self,
                    options={
                        **self.options,
                        "order_with_respect_to": operation.order_with_respect_to,
                    },
                ),
            ]
        elif (
            isinstance(operation, FieldOperation)
            and self.name_lower == operation.model_name_lower
        ):
            if isinstance(operation, AddField):
                return [
                    replace(
                        self,
                        fields=[*self.fields, (operation.name, operation.field)],
                    ),
                ]
            elif isinstance(operation, AlterField):
                return [
                    replace(
                        self,
                        fields=[
                            (n, operation.field if n == operation.name else v)
                            for n, v in self.fields
                        ],
                    ),
                ]
            elif isinstance(operation, RemoveField):
                options = self.options.copy()
                for option_name in ("unique_together", "index_together"):
                    option = options.pop(option_name, None)
                    if option:
                        option = set(
                            filter(
                                bool,
                                (
                                    tuple(
                                        f for f in fields if f != operation.name_lower
                                    )
                                    for fields in option
                                ),
                            )
                        )
                        if option:
                            options[option_name] = option
                order_with_respect_to = options.get("order_with_respect_to")
                if order_with_respect_to == operation.name_lower:
                    del options["order_with_respect_to"]
                return [
                    replace(
                        self,
                        fields=[
                            (n, v)
                            for n, v in self.fields
                            if n.lower() != operation.name_lower
                        ],
                        options=options,
                    ),
                ]
            elif isinstance(operation, RenameField):
                options = self.options.copy()
                for option_name in ("unique_together", "index_together"):
                    option = options.get(option_name)
                    if option:
                        options[option_name] = {
                            tuple(
                                operation.new_name if f == operation.old_name else f
                                for f in fields
                            )
                            for fields in option
                        }
                order_with_respect_to = options.get("order_with_respect_to")
                if order_with_respect_to == operation.old_name:
                    options["order_with_respect_to"] = operation.new_name
                return [
                    replace(
                        self,
                        fields=[
                            (operation.new_name if n == operation.old_name else n, v)
                            for n, v in self.fields
                        ],
                        options=options,
                    ),
                ]
        elif (
            isinstance(operation, IndexOperation)
            and self.name_lower == operation.model_name_lower
        ):
            if isinstance(operation, AddIndex):
                return [
                    replace(
                        self,
                        options={
                            **self.options,
                            "indexes": [
                                *self.options.get("indexes", []),
                                operation.index,
                            ],
                        },
                    ),
                ]
            elif isinstance(operation, RemoveIndex):
                options_indexes = [
                    index
                    for index in self.options.get("indexes", [])
                    if index.name != operation.name
                ]
                return [
                    replace(
                        self,
                        options={
                            **self.options,
                            "indexes": options_indexes,
                        },
                    ),
                ]
            elif isinstance(operation, AddConstraint):
                return [
                    replace(
                        self,
                        options={
                            **self.options,
                            "constraints": [
                                *self.options.get("constraints", []),
                                operation.constraint,
                            ],
                        },
                    ),
                ]
            elif isinstance(operation, AlterConstraint):
                options_constraints = [
                    constraint
                    for constraint in self.options.get("constraints", [])
                    if constraint.name != operation.name
                ] + [operation.constraint]
                return [
                    replace(
                        self,
                        options={
                            **self.options,
                            "constraints": options_constraints,
                        },
                    ),
                ]
            elif isinstance(operation, RemoveConstraint):
                options_constraints = [
                    constraint
                    for constraint in self.options.get("constraints", [])
                    if constraint.name != operation.name
                ]
                return [
                    replace(
                        self,
                        options={
                            **self.options,
                            "constraints": options_constraints,
                        },
                    ),
                ]
        return super().reduce(operation, app_label)