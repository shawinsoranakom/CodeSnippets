def _setup_models__(self, cr: BaseCursor, model_names: Iterable[str] | None = None) -> None:  # noqa: PLW3201
        """ Perform the setup of models.
        This must be called after loading modules and before using the ORM.

        When given ``model_names``, it performs an incremental setup: only the
        models impacted by the given ``model_names`` and all the already-marked
        models will be set up. Otherwise, all models are set up.
        """
        from .environments import Environment  # noqa: PLC0415
        env = Environment(cr, SUPERUSER_ID, {})
        env.invalidate_all()

        # Uninstall registry hooks. Because of the condition, this only happens
        # on a fully loaded registry, and not on a registry being loaded.
        if self.ready:
            for model in env.values():
                model._unregister_hook()

        # clear cache to ensure consistency, but do not signal it
        for cache in self.__caches.values():
            cache.clear()

        reset_cached_properties(self)
        self._field_trigger_trees.clear()
        self._is_modifying_relations.clear()
        self.registry_invalidated = True

        # model classes on which to *not* recompute field_depends[_context]
        models_field_depends_done = set()

        if model_names is None:
            self.many2many_relations.clear()
            self.field_setup_dependents.clear()

            # mark all models for setup
            for model_cls in self.models.values():
                model_cls._setup_done__ = False

            self.field_depends.clear()
            self.field_depends_context.clear()

        else:
            # only mark impacted models for setup and invalidate related fields
            model_names_to_setup = self.descendants(model_names, '_inherit', '_inherits')
            for fields in self.many2many_relations.values():
                for pair in list(fields):
                    if pair[0] in model_names_to_setup:
                        fields.discard(pair)

            for model_name in model_names_to_setup:
                self[model_name]._setup_done__ = False

            # recursively mark fields to re-setup
            todo = []
            for model_cls in self.models.values():
                if model_cls._custom:
                    # custom models are going to be reloaded and set up below
                    model_cls._setup_done__ = False
                if model_cls._setup_done__:
                    models_field_depends_done.add(model_cls)
                else:
                    todo.extend(model_cls._fields.values())

            done = set()
            for field in todo:
                if field in done:
                    continue

                model_cls = self[field.model_name]
                if model_cls._setup_done__ and field._base_fields__:
                    # the field has been created by model_classes._setup() as
                    # Field(_base_fields__=...); restore it to force its setup
                    name = field.name
                    base_fields = field._base_fields__

                    field.__dict__.clear()
                    field.__init__(_base_fields__=base_fields)
                    field._toplevel = True
                    field.__set_name__(model_cls, name)
                    field._setup_done = False

                    models_field_depends_done.discard(model_cls)

                # partial invalidation of field_depends[_context]
                self.field_depends.pop(field, None)
                self.field_depends_context.pop(field, None)

                done.add(field)
                todo.extend(self.field_setup_dependents.pop(field, ()))

        self.many2one_company_dependents.clear()

        model_classes.setup_model_classes(env)

        # determine field_depends and field_depends_context
        for model_cls in self.models.values():
            if model_cls in models_field_depends_done:
                continue
            model = model_cls(env, (), ())
            for field in model._fields.values():
                depends, depends_context = field.get_depends(model)
                self.field_depends[field] = tuple(depends)
                self.field_depends_context[field] = tuple(depends_context)

        # clean the lazy_property again in case they are cached by another ongoing registry readonly request
        reset_cached_properties(self)

        # Reinstall registry hooks. Because of the condition, this only happens
        # on a fully loaded registry, and not on a registry being loaded.
        if self.ready:
            for model in env.values():
                model._register_hook()
            env.flush_all()