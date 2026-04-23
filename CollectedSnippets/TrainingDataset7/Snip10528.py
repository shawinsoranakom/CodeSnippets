def render_multiple(self, model_states):
        # We keep trying to render the models in a loop, ignoring invalid
        # base errors, until the size of the unrendered models doesn't
        # decrease by at least one, meaning there's a base dependency loop/
        # missing base.
        if not model_states:
            return
        # Prevent that all model caches are expired for each render.
        with self.bulk_update():
            unrendered_models = model_states
            while unrendered_models:
                new_unrendered_models = []
                for model in unrendered_models:
                    try:
                        model.render(self)
                    except InvalidBasesError:
                        new_unrendered_models.append(model)
                if len(new_unrendered_models) == len(unrendered_models):
                    raise InvalidBasesError(
                        "Cannot resolve bases for %r\nThis can happen if you are "
                        "inheriting models from an app with migrations (e.g. "
                        "contrib.auth)\n in an app with no migrations; see "
                        "https://docs.djangoproject.com/en/%s/topics/migrations/"
                        "#dependencies for more"
                        % (new_unrendered_models, get_docs_version())
                    )
                unrendered_models = new_unrendered_models