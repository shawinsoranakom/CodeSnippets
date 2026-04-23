def add_code_part(
            code_part: str, guard: Guard | None, log_only: bool = False
        ) -> None:
            verbose_code_part = get_verbose_code_part(code_part, guard)
            guards_log.debug("%s", verbose_code_part)

            structured_guard_fns.append(
                lambda: {
                    "code": code_part,
                    "stack": (
                        structured.from_traceback(guard.stack.summary())
                        if guard and guard.stack
                        else None
                    ),
                    "user_stack": (
                        structured.from_traceback(guard.user_stack)
                        if guard and guard.user_stack
                        else None
                    ),
                }
            )

            if verbose_guards_log.isEnabledFor(logging.DEBUG):
                maybe_stack = ""
                maybe_user_stack = ""
                if guard is not None:
                    if guard.stack:
                        maybe_stack = f"\nStack:\n{''.join(guard.stack.format())}"
                    if guard.user_stack:
                        maybe_user_stack = (
                            f"\nUser stack:\n{''.join(guard.user_stack.format())}"
                        )
                verbose_guards_log.debug(
                    "Guard: %s%s%s",
                    code_part,
                    maybe_stack,
                    maybe_user_stack,
                )

            if not log_only:
                code_parts.append(code_part)
                verbose_code_parts.append(verbose_code_part)