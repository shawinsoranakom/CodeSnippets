def set_state_tree(self, state_tree):
        """Assigns values to variables of the model.

        This method takes a dictionary of nested variable values, which
        represents the state tree of the model, and assigns them to the
        corresponding variables of the model. The dictionary keys represent the
        variable names (e.g., `'trainable_variables'`, `'optimizer_variables'`),
        and the values are nested dictionaries containing the variable
        paths and their corresponding values.

        Args:
            state_tree: A dictionary representing the state tree of the model.
                The keys are the variable names, and the values are nested
                dictionaries representing the variable paths and their values.
        """
        for k, v in state_tree.items():
            path_value_dict = self._flatten_nested_dict(v)
            if k == "trainable_variables":
                self._assign_variable_values(
                    self.trainable_variables, path_value_dict
                )
            elif k == "non_trainable_variables":
                self._assign_variable_values(
                    self.non_trainable_variables, path_value_dict
                )
            elif k == "optimizer_variables":
                if hasattr(self, "optimizer") and self.optimizer is not None:
                    self._assign_variable_values(
                        self.optimizer.variables, path_value_dict
                    )
            elif k == "metrics_variables":
                if (
                    hasattr(self, "metrics_variables")
                    and self.metrics_variables
                ):
                    self._assign_variable_values(
                        self.metrics_variables, path_value_dict
                    )
            else:
                raise ValueError(f"Unknown variable name: {k}")