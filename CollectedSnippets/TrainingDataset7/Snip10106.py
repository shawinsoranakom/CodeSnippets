def create_altered_constraints(self):
        option_name = operations.AddConstraint.option_name
        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get(
                (app_label, model_name), model_name
            )
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]

            old_constraints = old_model_state.options[option_name]
            new_constraints = new_model_state.options[option_name]

            alt_constraints = []
            alt_constraints_name = []

            for old_c in old_constraints:
                for new_c in new_constraints:
                    old_c_dec = old_c.deconstruct()
                    new_c_dec = new_c.deconstruct()
                    if (
                        old_c_dec != new_c_dec
                        and old_c.name == new_c.name
                        and not self._constraint_should_be_dropped_and_recreated(
                            old_c, new_c
                        )
                    ):
                        alt_constraints.append(new_c)
                        alt_constraints_name.append(new_c.name)

            add_constraints = [
                c
                for c in new_constraints
                if c not in old_constraints and c.name not in alt_constraints_name
            ]
            rem_constraints = [
                c
                for c in old_constraints
                if c not in new_constraints and c.name not in alt_constraints_name
            ]

            self.altered_constraints.update(
                {
                    (app_label, model_name): {
                        "added_constraints": add_constraints,
                        "removed_constraints": rem_constraints,
                        "altered_constraints": alt_constraints,
                    }
                }
            )