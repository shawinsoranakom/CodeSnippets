def DUPLICATE_INPUT(self, guard: Guard, source_b: Source) -> None:
        if is_from_skip_guard_source(
            guard.originating_source
        ) or is_from_skip_guard_source(source_b):
            return

        if self.save_guards:
            if name := get_local_source_name(source_b):
                self.check_fn_manager.additional_used_local_vars.add(name)
            if name := get_global_source_name(source_b):
                self.check_fn_manager.additional_used_global_vars.add(name)

        ref_a = self.arg_ref(guard)
        ref_b = self.arg_ref(source_b.name)

        if is_from_optimizer_source(
            guard.originating_source
        ) or is_from_optimizer_source(source_b):
            return

        # Check that the guard has not been inserted already
        key = (ref_a, ref_b)
        if key in self._cached_duplicate_input_guards:
            return

        self._cached_duplicate_input_guards.add((ref_a, ref_b))
        self._cached_duplicate_input_guards.add((ref_b, ref_a))

        code = [f"{ref_b} is {ref_a}"]
        self._set_guard_export_info(guard, code)

        if config.use_lamba_guard_for_object_aliasing:
            # Save the code part so that we can install a lambda guard at the
            # end.  Read the Note - On Lambda guarding of object aliasing - to
            # get more information.
            code_part = code[0]
            verbose_code_part = get_verbose_code_parts(code_part, guard)[0]
            self.object_aliasing_guard_codes.append((code_part, verbose_code_part))
        else:
            install_object_aliasing_guard(
                self.get_guard_manager(guard),
                self.get_guard_manager_from_source(source_b),
                get_verbose_code_parts(code, guard),
                guard.user_stack,
            )