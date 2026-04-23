def get_expanded_tied_weights_keys(self, all_submodels: bool = False) -> dict:
        r"""
        Return the expanded tied weight keys (in case they contain modules or regex patterns) for only the current
        model, or recursively for all submodels if `all_submodels=True` (i.e. it will re-check the config values for all
        submodels).

        For almost all models, we only require to tie the embeddings, so the model has an internal property
        `_tied_weights_keys = {"lm_head.weight": "model.embed_tokens.weight"}`. In this case, the mapping is already
        "expanded", i.e. it already contains full parameters, and this function will simply return a copy of the property.
        For more complex patterns, e.g. for `DFineForObjectDetection`, we have the following attribute
        ```
        _tied_weights_keys = {
            r"bbox_embed.(?![0])\d+": "bbox_embed.0",
            r"class_embed.(?![0])\d+": "class_embed.0",
            "model.decoder.class_embed": "class_embed",
            "model.decoder.bbox_embed": "bbox_embed",
        }
        ```
        In this case, the function looks up all the model's parameters and buffers, and matches all the params,
        returning the following:
        ```
        {
            'bbox_embed.1.layers.0.bias': 'bbox_embed.0.layers.0.bias',
            'bbox_embed.1.layers.0.weight': 'bbox_embed.0.layers.0.weight',
            'bbox_embed.1.layers.1.bias': 'bbox_embed.0.layers.1.bias',
            'bbox_embed.1.layers.1.weight': 'bbox_embed.0.layers.1.weight',
            'bbox_embed.1.layers.2.bias': 'bbox_embed.0.layers.2.bias',
            'bbox_embed.1.layers.2.weight': 'bbox_embed.0.layers.2.weight',
            'bbox_embed.2.layers.0.bias': 'bbox_embed.0.layers.0.bias',
            'bbox_embed.2.layers.0.weight': 'bbox_embed.0.layers.0.weight',
            ...
            'class_embed.1.bias': 'class_embed.0.bias',
            'class_embed.1.weight': 'class_embed.0.weight',
            'class_embed.2.bias': 'class_embed.0.bias',
            'class_embed.2.weight': 'class_embed.0.weight',
            ...
            'model.decoder.class_embed.0.bias': 'class_embed.0.bias',
            'model.decoder.class_embed.0.weight': 'class_embed.0.weight',
            'model.decoder.class_embed.1.bias': 'class_embed.0.bias',
            'model.decoder.class_embed.1.weight': 'class_embed.0.weight',
            ...
            'model.decoder.bbox_embed.0.layers.0.bias': 'bbox_embed.0.layers.0.bias',
            'model.decoder.bbox_embed.0.layers.0.weight': 'bbox_embed.0.layers.0.weight',
            'model.decoder.bbox_embed.0.layers.1.bias': 'bbox_embed.0.layers.1.bias',
            'model.decoder.bbox_embed.0.layers.1.weight': 'bbox_embed.0.layers.1.weight',
            ...
        }
        ```
        i.e. all the parameters matching the regex and modules patterns in `_tied_weights_keys`
        """
        if all_submodels:
            expanded_tied_weights = {}
            for prefix, submodule in self.named_modules(remove_duplicate=False):
                if isinstance(submodule, PreTrainedModel):
                    # Will dynamically check the config if it has changed
                    submodel_tied_weights = submodule.get_expanded_tied_weights_keys(all_submodels=False)
                    if prefix != "":
                        submodel_tied_weights = {
                            f"{prefix}.{k}": f"{prefix}.{v}" for k, v in submodel_tied_weights.items()
                        }
                    expanded_tied_weights.update(submodel_tied_weights)
            return expanded_tied_weights

        tied_mapping = self._tied_weights_keys
        # If the config does not specify any tying, return empty dict
        # NOTE: not all modules have `tie_word_embeddings` attr, for example vision-only
        # modules do not have any word embeddings!
        tie_word_embeddings = getattr(self.config, "tie_word_embeddings", False)
        if not tie_word_embeddings:
            return {}
        # If None, return empty dict
        elif tied_mapping is None:
            return {}
        # Short-cut for the most common cases: if the tied weights mapping only contains already expanded params,
        # return it directly (the regex matches names containing only letters, numbers, dots, and underscores to make
        # sure it does not contain a regex pattern, and finishing by "bias" or "weight" to make sure it's not a module)
        common_case_regex = re.compile(r"^[A-Za-z0-9_\.]+(weight)|(bias)$")
        if all(common_case_regex.match(k) for k in tied_mapping.keys() | tied_mapping.values()):
            return tied_mapping.copy()

        # We need to expand the regex patterns or the modules into proper parameters
        expanded_tied_weights = {}
        all_param_names = {k for k, _ in self.named_parameters(remove_duplicate=False)} | {
            k for k, _ in self.named_buffers(remove_duplicate=False)
        }
        for target_name, source_name in tied_mapping.items():
            target_name = "^" + target_name
            source_name = "^" + source_name

            source_params = sorted(filter(lambda x: re.search(source_name, x), all_param_names))
            target_params = sorted(filter(lambda x: re.search(target_name, x), all_param_names))
            if (
                not len(source_params) > 0
                or not len(target_params) > 0
                or len(target_params) % len(source_params) != 0
            ):
                raise ValueError(
                    f"There is an issue with your definition of `tie_weights_keys` for {source_name}:{target_name}. "
                    f"We found {source_params} to tie into {target_params}"
                )
            # we cycle source as it should be dispatch in many target if regex
            for target_n, source_n in zip(target_params, cycle(source_params)):
                # If the source is already registered as a target, use the original corresponding source. This should never
                # happen in general, but some models such as `d_fine` have complicated regex patterns, so it end up being
                # the case for simplicity of the regexes. Fix it silently here
                if source_n in expanded_tied_weights.keys():
                    # Use original source instead of having keys both as source and targets
                    expanded_tied_weights[target_n] = expanded_tied_weights[source_n]
                # Usual case, everything is already correct
                else:
                    expanded_tied_weights[target_n] = source_n

        return expanded_tied_weights