def resolve_expression(
        self,
        query=None,
        allow_joins=True,
        reuse=None,
        summarize=False,
        for_save=False,
    ):
        expressions = list(self.flatten())
        # Split expressions and wrappers.
        index_expressions, wrappers = partition(
            lambda e: isinstance(e, self.wrapper_classes),
            expressions,
        )
        wrapper_types = [type(wrapper) for wrapper in wrappers]
        if len(wrapper_types) != len(set(wrapper_types)):
            raise ValueError(
                "Multiple references to %s can't be used in an indexed "
                "expression."
                % ", ".join(
                    [wrapper_cls.__qualname__ for wrapper_cls in self.wrapper_classes]
                )
            )
        if expressions[1 : len(wrappers) + 1] != wrappers:
            raise ValueError(
                "%s must be topmost expressions in an indexed expression."
                % ", ".join(
                    [wrapper_cls.__qualname__ for wrapper_cls in self.wrapper_classes]
                )
            )
        # Wrap expressions in parentheses if they are not column references.
        root_expression = index_expressions[1]
        resolve_root_expression = root_expression.resolve_expression(
            query,
            allow_joins,
            reuse,
            summarize,
            for_save,
        )
        if not isinstance(resolve_root_expression, Col):
            root_expression = Func(root_expression, template="(%(expressions)s)")

        if wrappers:
            # Order wrappers and set their expressions.
            wrappers = sorted(
                wrappers,
                key=lambda w: self.wrapper_classes.index(type(w)),
            )
            wrappers = [wrapper.copy() for wrapper in wrappers]
            for i, wrapper in enumerate(wrappers[:-1]):
                wrapper.set_source_expressions([wrappers[i + 1]])
            # Set the root expression on the deepest wrapper.
            wrappers[-1].set_source_expressions([root_expression])
            self.set_source_expressions([wrappers[0]])
        else:
            # Use the root expression, if there are no wrappers.
            self.set_source_expressions([root_expression])
        return super().resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )