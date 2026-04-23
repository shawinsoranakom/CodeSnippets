def get_traceback_frame_variables(self, request, tb_frame):
        """
        Replace the values of variables marked as sensitive with
        stars (*********).
        """
        sensitive_variables = None

        # Coroutines don't have a proper `f_back` so they need to be inspected
        # separately. Handle this by stashing the registered sensitive
        # variables in a global dict indexed by `hash(file_path:line_number)`.
        if (
            tb_frame.f_code.co_flags & inspect.CO_COROUTINE != 0
            and tb_frame.f_code.co_name != "sensitive_variables_wrapper"
        ):
            key = hash(
                f"{tb_frame.f_code.co_filename}:{tb_frame.f_code.co_firstlineno}"
            )
            sensitive_variables = coroutine_functions_to_sensitive_variables.get(
                key, None
            )

        if sensitive_variables is None:
            # Loop through the frame's callers to see if the
            # sensitive_variables decorator was used.
            current_frame = tb_frame
            while current_frame is not None:
                if (
                    current_frame.f_code.co_name == "sensitive_variables_wrapper"
                    and "sensitive_variables_wrapper" in current_frame.f_locals
                ):
                    # The sensitive_variables decorator was used, so take note
                    # of the sensitive variables' names.
                    wrapper = current_frame.f_locals["sensitive_variables_wrapper"]
                    sensitive_variables = getattr(wrapper, "sensitive_variables", None)
                    break
                current_frame = current_frame.f_back

        cleansed = {}
        if self.is_active(request) and sensitive_variables:
            if sensitive_variables == "__ALL__":
                # Cleanse all variables
                for name in tb_frame.f_locals:
                    cleansed[name] = self.cleansed_substitute
            else:
                # Cleanse specified variables
                for name, value in tb_frame.f_locals.items():
                    if name in sensitive_variables:
                        value = self.cleansed_substitute
                    else:
                        value = self.cleanse_special_types(request, value)
                    cleansed[name] = value
        else:
            # Potentially cleanse the request and any MultiValueDicts if they
            # are one of the frame variables.
            for name, value in tb_frame.f_locals.items():
                cleansed[name] = self.cleanse_special_types(request, value)

        if (
            tb_frame.f_code.co_name == "sensitive_variables_wrapper"
            and "sensitive_variables_wrapper" in tb_frame.f_locals
        ):
            # For good measure, obfuscate the decorated function's arguments in
            # the sensitive_variables decorator's frame, in case the variables
            # associated with those arguments were meant to be obfuscated from
            # the decorated function's frame.
            cleansed["func_args"] = self.cleansed_substitute
            cleansed["func_kwargs"] = self.cleansed_substitute

        return cleansed.items()