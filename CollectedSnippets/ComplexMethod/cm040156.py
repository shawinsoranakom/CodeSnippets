def add_optimizer_variables(
        self, trainable_variables, name, initializer="zeros"
    ):
        """Add optimizer variables from the list of trainable model variables.

        Create an optimizer variable based on the information of the supplied
        model variables.  For example, in SGD optimizer momemtum, for each model
        variable, a corresponding momemtum variable is created of the same shape
        and dtype.

        Note that trainable variables with `v.overwrite_with_gradient == True`
        will insert `None`, into the output list, since the optimizer variable
        will not be used anyways, and could be wasteful.

        Args:
            trainable_variables: `keras.Variable`, the corresponding model
                variable to the optimizer variable to be created.
            name: The name prefix(es) of the optimizer variable(s) to be
                created. Can be a single string or list of strings.  If a
                list of strings, will create an optimizer variable for each
                prefix.  The variable name will follow the pattern
                `{variable_name}_{trainable_variable.name}`, e.g.,
                `momemtum/dense_1`.
            initializer: Initializer object(s) to use to populate the initial
                variable value(s), or string name of a built-in initializer
                (e.g. `"random_normal"`). If unspecified, defaults to
                `"zeros"`.

        Returns:
            A list of optimizer variables, in the format of `keras.Variable`s.
            If multiple names are provide, returns a tuple of lists.
        """
        name_list = name
        initializer_list = initializer
        if isinstance(name, str):
            # Single name/initializer.
            name_list = [name]
            initializer_list = [initializer]
        else:
            # Multiple names/initializers.
            # If there is only one initializer, use it for all names.
            if isinstance(initializer, str) or isinstance(
                initializer, initializers.Initializer
            ):
                initializer_list = [initializer] * len(name_list)

        if len(name_list) != len(initializer_list):
            raise ValueError(
                f"The number of provided names must match the number of "
                f"provided initializers.  Received name='{name}', "
                f"initializer='{initializer}'"
            )

        # Build up lists of optimizer variables.
        optimizer_variables = tuple([] for _ in name_list)
        for variable in trainable_variables:
            # Interleaves adding variables for backward-compatibility.
            if not self._overwrite_variable_with_gradient(variable):
                for i, (var_name, var_init) in enumerate(
                    zip(name_list, initializer_list)
                ):
                    optimizer_variables[i].append(
                        self.add_variable_from_reference(
                            variable,
                            name=var_name,
                            initializer=var_init,
                        )
                    )
            else:
                for i in range(len(name_list)):
                    optimizer_variables[i].append(None)

        # If single input name, return the single list.
        if isinstance(name, str):
            return optimizer_variables[0]

        return optimizer_variables