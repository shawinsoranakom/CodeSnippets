def _check_loop_control(self) -> None:
        """Check loop_control configuration for potential problems."""
        task_ctx = TaskContext.current()

        loop_variables = dict(
            loop_var=self._task.loop_control.loop_var,
            index_var=self._task.loop_control.index_var,
        )

        # These reserved variables are set in TaskContext.start_loop,
        # so shouldn't be expected to already be in task variables.
        reserved_loop_variables = {
            "ansible_index_var",
            "ansible_loop",
            "ansible_loop_var",
        }

        duplicate_loop_variables = {
            key for key, group in itertools.groupby(sorted(value for value in loop_variables.values() if value)) if len(list(group)) > 1
        }

        for var_name, var_value in loop_variables.items():
            if not var_value:
                continue

            if var_value in task_ctx.task_vars:
                conflict = "already in use"
            elif var_value in reserved_loop_variables:
                conflict = "reserved"
            elif var_value in C.COMMON_CONNECTION_VARS:
                conflict = "reserved"
            elif var_value in duplicate_loop_variables:
                conflict = "used more than once"
            else:
                continue

            display.warning(
                msg=f"The variable {var_value!r} is {conflict}.",
                help_text=f"You should set the `{var_name}` value in the `loop_control` option for the task "
                          "to something else to avoid variable collisions and unexpected behavior.",
                obj=var_value,
            )