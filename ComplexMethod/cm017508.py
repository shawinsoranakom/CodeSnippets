def get_for_models(self, *models, for_concrete_models=True):
        """
        Given *models, return a dictionary mapping {model: content_type}.
        """
        results = {}
        # Models that aren't already in the cache grouped by app labels.
        needed_models = defaultdict(set)
        # Mapping of opts to the list of models requiring it.
        needed_opts = defaultdict(list)
        for model in models:
            opts = self._get_opts(model, for_concrete_models)
            try:
                ct = self._get_from_cache(opts)
            except KeyError:
                needed_models[opts.app_label].add(opts.model_name)
                needed_opts[(opts.app_label, opts.model_name)].append(model)
            else:
                results[model] = ct
        if needed_opts:
            # Lookup required content types from the DB.
            condition = Q(
                *(
                    Q(("app_label", app_label), ("model__in", models))
                    for app_label, models in needed_models.items()
                ),
                _connector=Q.OR,
            )
            cts = self.filter(condition)
            for ct in cts:
                opts_models = needed_opts.pop((ct.app_label, ct.model), [])
                for model in opts_models:
                    results[model] = ct
                self._add_to_cache(self.db, ct)
        # Create content types that weren't in the cache or DB.
        for (app_label, model_name), opts_models in needed_opts.items():
            ct = self.create(app_label=app_label, model=model_name)
            self._add_to_cache(self.db, ct)
            for model in opts_models:
                results[model] = ct
        return results