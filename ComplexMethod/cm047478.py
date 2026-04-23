def resolve_depends(self, registry: Registry) -> Iterator[tuple[Field, ...]]:
        """ Return the dependencies of `self` as a collection of field tuples. """
        Model0 = registry[self.model_name]

        for dotnames in registry.field_depends[self]:
            field_seq: list[Field] = []
            model_name = self.model_name
            check_precompute = self.precompute

            for index, fname in enumerate(dotnames.split('.')):
                Model = registry[model_name]
                if Model0._transient and not Model._transient:
                    # modifying fields on regular models should not trigger
                    # recomputations of fields on transient models
                    break

                try:
                    field = Model._fields[fname]
                except KeyError:
                    raise ValueError(
                        f"Wrong @depends on '{self.compute}' (compute method of field {self}). "
                        f"Dependency field '{fname}' not found in model {model_name}."
                    ) from None
                if field is self and index and not self.recursive:
                    self.recursive = True
                    warnings.warn(f"Field {self} should be declared with recursive=True", stacklevel=1)

                # precomputed fields can depend on non-precomputed ones, as long
                # as they are reachable through at least one many2one field
                if check_precompute and field.store and field.compute and not field.precompute:
                    warnings.warn(f"Field {self} cannot be precomputed as it depends on non-precomputed field {field}", stacklevel=1)
                    self.precompute = False

                if field_seq and not field_seq[-1]._description_searchable:
                    # the field before this one is not searchable, so there is
                    # no way to know which on records to recompute self
                    warnings.warn(
                        f"Field {field_seq[-1]!r} in dependency of {self} should be searchable. "
                        f"This is necessary to determine which records to recompute when {field} is modified. "
                        f"You should either make the field searchable, or simplify the field dependency.",
                        stacklevel=1,
                    )

                field_seq.append(field)

                # do not make self trigger itself: for instance, a one2many
                # field line_ids with domain [('foo', ...)] will have
                # 'line_ids.foo' as a dependency
                if not (field is self and not index):
                    yield tuple(field_seq)

                if field.type == 'one2many':
                    for inv_field in Model.pool.field_inverses[field]:
                        yield tuple(field_seq) + (inv_field,)

                if check_precompute and field.type == 'many2one':
                    check_precompute = False

                model_name = field.comodel_name