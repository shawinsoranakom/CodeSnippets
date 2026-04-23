def pipeline_parallel(self):
        """
        Apply the model's pipeline parallelization plan.
        """
        if self.pp_group.world_size <= 1:
            return

        if not self.model.supports_pp_plan:
            tip = get_feature_request_tip(
                self.model_config.model, self.model_config.trust_remote_code
            )
            raise ValueError(
                f"{type(self.model)} does not support pipeline parallel. {tip}"
            )

        def attrsetter(attr: str) -> Callable[[object, object], None]:
            """Set a possibly nested attribute, like the inverse of attrgetter."""
            parent, _, name = attr.rpartition(".")

            def setter(obj: object, value: object):
                attr_parent = attrgetter(parent)(obj) if parent else obj
                setattr(attr_parent, name, value)

            return setter

        module_lists = []
        module_list_idx = None
        pp_plan = list(self.model._pp_plan.keys())
        for i, name in enumerate(pp_plan):
            # attrgetter in case the module is nested (e.g. "text_model.layers")
            if isinstance(attrgetter(name)(self.model), nn.ModuleList):
                module_lists.append(name)
                module_list_idx = i

        if len(module_lists) > 1:
            raise ValueError(
                "Pipeline parallel of models with multiple `ModuleList`s "
                "in the base model are not supported yet!"
            )
        if module_list_idx is None:
            raise ValueError(f"Could not find `ModuleList` in {type(self.model)}")

        # Layers before module list
        for name in pp_plan[:module_list_idx]:
            if self.pp_group.is_first_rank or (
                self._get_tie_word_embeddings() and self.pp_group.is_last_rank
            ):
                continue
            # attrsetter in case the module is nested (e.g. "text_model.embed_tokens")
            attrsetter(name)(self.model, PPMissingLayer())

        # Module list
        start_layer, end_layer = get_pp_indices(
            self.text_config.num_hidden_layers,
            self.pp_group.rank_in_group,
            self.pp_group.world_size,
        )
        layers_name = pp_plan[module_list_idx]
        # attrgetter in case the module is nested (e.g. "text_model.layers")
        layers = attrgetter(layers_name)(self.model)
        for i in range(len(layers)):
            if start_layer <= i and i < end_layer:
                continue
            layers[i] = PPMissingLayer()

        # Layers after module list
        for name in pp_plan[module_list_idx + 1 :]:
            # Modules that should be on last rank
            if not self.pp_group.is_last_rank:
                # attrsetter in case the module is nested (e.g. "text_model.norm")
                attrsetter(name)(self.model, PPMissingLayer())