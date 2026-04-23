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