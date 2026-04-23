def get_depends(self, model: BaseModel) -> tuple[Iterable[str], Iterable[str]]:
        """ Return the field's dependencies and cache dependencies. """
        if self._depends is not None:
            # the parameter 'depends' has priority over 'depends' on compute
            return self._depends, self._depends_context or ()

        if self.related:
            if self._depends_context is not None:
                depends_context = self._depends_context
            else:
                depends_context = []
                field_model_name = model._name
                for field_name in self.related.split('.'):
                    field_model = model.env[field_model_name]
                    field = field_model._fields[field_name]
                    depends_context.extend(field.get_depends(field_model)[1])
                    field_model_name = field.comodel_name
                depends_context = tuple(unique(depends_context))
            return [self.related], depends_context

        if not self.compute:
            return (), self._depends_context or ()

        # determine the functions implementing self.compute
        if isinstance(self.compute, str):
            funcs = resolve_mro(model, self.compute, callable)
        else:
            funcs = [self.compute]

        # collect depends and depends_context
        depends = []
        depends_context = list(self._depends_context or ())
        for func in funcs:
            deps = getattr(func, '_depends', ())
            depends.extend(deps(model) if callable(deps) else deps)
            depends_context.extend(getattr(func, '_depends_context', ()))

        return depends, depends_context