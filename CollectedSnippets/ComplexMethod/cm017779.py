def get_objects(count_only=False):
            """
            Collate the objects to be serialized. If count_only is True, just
            count the number of objects to be serialized.
            """
            if use_natural_foreign_keys:
                models = serializers.sort_dependencies(
                    app_list.items(), allow_cycles=True
                )
            else:
                # There is no need to sort dependencies when natural foreign
                # keys are not used.
                models = []
                for app_config, model_list in app_list.items():
                    if model_list is None:
                        models.extend(app_config.get_models())
                    else:
                        models.extend(model_list)
            for model in models:
                if model in excluded_models:
                    continue
                if model._meta.proxy and model._meta.proxy_for_model not in models:
                    warnings.warn(
                        "%s is a proxy model and won't be serialized."
                        % model._meta.label,
                        category=ProxyModelWarning,
                    )
                if not model._meta.proxy and router.allow_migrate_model(using, model):
                    if use_base_manager:
                        objects = model._base_manager
                    else:
                        objects = model._default_manager

                    queryset = objects.using(using).order_by(model._meta.pk.name)
                    if primary_keys:
                        queryset = queryset.filter(pk__in=primary_keys)
                    if count_only:
                        yield queryset.order_by().count()
                    else:
                        chunk_size = (
                            2000 if queryset._prefetch_related_lookups else None
                        )
                        yield from queryset.iterator(chunk_size=chunk_size)