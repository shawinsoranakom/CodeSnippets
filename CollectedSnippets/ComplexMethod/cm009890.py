def validate_chains(cls, values: dict) -> Any:
        """Validate that the correct inputs exist for all chains."""
        chains = values["chains"]
        input_variables = values["input_variables"]
        memory_keys = []
        if "memory" in values and values["memory"] is not None:
            """Validate that prompt input variables are consistent."""
            memory_keys = values["memory"].memory_variables
            if set(input_variables).intersection(set(memory_keys)):
                overlapping_keys = set(input_variables) & set(memory_keys)
                msg = (
                    f"The input key(s) {''.join(overlapping_keys)} are found "
                    f"in the Memory keys ({memory_keys}) - please use input and "
                    f"memory keys that don't overlap."
                )
                raise ValueError(msg)

        known_variables = set(input_variables + memory_keys)

        for chain in chains:
            missing_vars = set(chain.input_keys).difference(known_variables)
            if chain.memory:
                missing_vars = missing_vars.difference(chain.memory.memory_variables)

            if missing_vars:
                msg = (
                    f"Missing required input keys: {missing_vars}, "
                    f"only had {known_variables}"
                )
                raise ValueError(msg)
            overlapping_keys = known_variables.intersection(chain.output_keys)
            if overlapping_keys:
                msg = f"Chain returned keys that already exist: {overlapping_keys}"
                raise ValueError(msg)

            known_variables |= set(chain.output_keys)

        if "output_variables" not in values:
            if values.get("return_all", False):
                output_keys = known_variables.difference(input_variables)
            else:
                output_keys = chains[-1].output_keys
            values["output_variables"] = output_keys
        else:
            missing_vars = set(values["output_variables"]).difference(known_variables)
            if missing_vars:
                msg = f"Expected output variables that were not found: {missing_vars}."
                raise ValueError(msg)

        return values