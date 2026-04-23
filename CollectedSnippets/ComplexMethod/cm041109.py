def resolve_model(self, model: dict) -> dict | None:
        resolved_model = copy.deepcopy(model)
        model_names = set()

        def _look_for_ref(sub_model):
            for key, value in sub_model.items():
                if key == "$ref":
                    ref_name = value.rsplit("/", maxsplit=1)[-1]
                    if ref_name == self.model_name:
                        # if we reference our main Model, use the # for recursive access
                        sub_model[key] = "#"
                        continue
                    # otherwise, this Model will be available in $defs
                    sub_model[key] = f"#/$defs/{ref_name}"

                    if ref_name != self._current_resolving_name:
                        # add the ref to the next ref to resolve and to $deps
                        model_names.add(ref_name)

                elif isinstance(value, dict):
                    _look_for_ref(value)
                elif isinstance(value, list):
                    for val in value:
                        if isinstance(val, dict):
                            _look_for_ref(val)

        if isinstance(resolved_model, dict):
            _look_for_ref(resolved_model)

        if model_names:
            for ref_model_name in model_names:
                if ref_model_name in self._deps:
                    continue

                def_resolved, was_resolved = self._get_resolved_submodel(model_name=ref_model_name)

                if not def_resolved:
                    LOG.debug(
                        "Failed to resolve submodel %s for model %s",
                        ref_model_name,
                        self._current_resolving_name,
                    )
                    return
                # if the ref was already resolved, we copy the result to not alter the already resolved schema
                if was_resolved:
                    def_resolved = copy.deepcopy(def_resolved)

                self._remove_self_ref(def_resolved)

                if "$deps" in def_resolved:
                    # this will happen only if the schema was already resolved, otherwise the deps would be in _deps
                    # remove own definition in case of recursive / circular Models
                    def_resolved["$defs"].pop(self.model_name, None)
                    # remove the $defs from the schema, we don't want nested $defs
                    def_resolved_defs = def_resolved.pop("$defs")
                    # merge the resolved sub model $defs to the main schema
                    self._deps.update(def_resolved_defs)

                # add the dependencies to the global $deps
                self._deps[ref_model_name] = def_resolved

        return resolved_model