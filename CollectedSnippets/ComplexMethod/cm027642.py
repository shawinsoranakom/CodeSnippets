async def _async_do_step_repeat(self) -> None:  # noqa: C901
        """Repeat a sequence helper."""
        description = self._action.get(CONF_ALIAS, "sequence")
        repeat = self._action[CONF_REPEAT]

        def set_repeat_var(
            iteration: int, count: int | None = None, item: Any = None
        ) -> None:
            repeat_vars = {"first": iteration == 1, "index": iteration}
            if count:
                repeat_vars["last"] = iteration == count
            if item is not None:
                repeat_vars["item"] = item
            self._variables.define_local("repeat", repeat_vars)

        script = self._script._get_repeat_script(self._step)  # noqa: SLF001
        warned_too_many_loops = False

        async def async_run_sequence(iteration: int, extra_msg: str = "") -> None:
            self._log("Repeating %s: Iteration %i%s", description, iteration, extra_msg)
            with trace_path("sequence"):
                await self._async_run_script(script)

        if CONF_COUNT in repeat:
            count = repeat[CONF_COUNT]
            if isinstance(count, template.Template):
                try:
                    count = int(count.async_render(self._variables))
                except (exceptions.TemplateError, ValueError) as ex:
                    self._log(
                        "Error rendering %s repeat count template: %s",
                        self._script.name,
                        ex,
                        level=logging.ERROR,
                    )
                    raise _AbortScript from ex
            extra_msg = f" of {count}"
            for iteration in range(1, count + 1):
                set_repeat_var(iteration, count)
                await async_run_sequence(iteration, extra_msg)
                if self._stop.done():
                    break

        elif CONF_FOR_EACH in repeat:
            try:
                items = template.render_complex(repeat[CONF_FOR_EACH], self._variables)
            except (exceptions.TemplateError, ValueError) as ex:
                self._log(
                    "Error rendering %s repeat for each items template: %s",
                    self._script.name,
                    ex,
                    level=logging.ERROR,
                )
                raise _AbortScript from ex

            if not isinstance(items, list):
                self._log(
                    "Repeat 'for_each' must be a list of items in %s, got: %s",
                    self._script.name,
                    items,
                    level=logging.ERROR,
                )
                raise _AbortScript("Repeat 'for_each' must be a list of items")

            count = len(items)
            for iteration, item in enumerate(items, 1):
                set_repeat_var(iteration, count, item)
                extra_msg = f" of {count} with item: {item!r}"
                if self._stop.done():
                    break
                await async_run_sequence(iteration, extra_msg)

        elif CONF_WHILE in repeat:
            conditions = [
                await self._async_get_condition(config) for config in repeat[CONF_WHILE]
            ]
            for iteration in itertools.count(1):
                set_repeat_var(iteration)
                if self._stop.done():
                    break
                if not self._test_conditions(conditions, "while"):
                    break

                if iteration > 1:
                    if iteration > REPEAT_WARN_ITERATIONS:
                        if not warned_too_many_loops:
                            warned_too_many_loops = True
                            self._log(
                                "While condition %s looped %s times",
                                repeat[CONF_WHILE],
                                REPEAT_WARN_ITERATIONS,
                                level=logging.WARNING,
                            )

                        if iteration > REPEAT_TERMINATE_ITERATIONS:
                            self._log(
                                "While condition %s terminated because it looped %s times",
                                repeat[CONF_WHILE],
                                REPEAT_TERMINATE_ITERATIONS,
                                level=logging.CRITICAL,
                            )
                            raise _AbortScript(
                                f"While condition {repeat[CONF_WHILE]} "
                                "terminated because it looped "
                                f" {REPEAT_TERMINATE_ITERATIONS} times"
                            )

                    # If the user creates a script with a tight loop,
                    # yield to the event loop so the system stays
                    # responsive while all the cpu time is consumed.
                    await asyncio.sleep(0)

                await async_run_sequence(iteration)

        elif CONF_UNTIL in repeat:
            conditions = [
                await self._async_get_condition(config) for config in repeat[CONF_UNTIL]
            ]
            for iteration in itertools.count(1):
                set_repeat_var(iteration)
                await async_run_sequence(iteration)
                if self._stop.done():
                    break
                if self._test_conditions(conditions, "until") in [True, None]:
                    break

                if iteration >= REPEAT_WARN_ITERATIONS:
                    if not warned_too_many_loops:
                        warned_too_many_loops = True
                        self._log(
                            "Until condition %s looped %s times",
                            repeat[CONF_UNTIL],
                            REPEAT_WARN_ITERATIONS,
                            level=logging.WARNING,
                        )

                    if iteration >= REPEAT_TERMINATE_ITERATIONS:
                        self._log(
                            "Until condition %s terminated because it looped %s times",
                            repeat[CONF_UNTIL],
                            REPEAT_TERMINATE_ITERATIONS,
                            level=logging.CRITICAL,
                        )
                        raise _AbortScript(
                            f"Until condition {repeat[CONF_UNTIL]} "
                            "terminated because it looped "
                            f"{REPEAT_TERMINATE_ITERATIONS} times"
                        )

                # If the user creates a script with a tight loop,
                # yield to the event loop so the system stays responsive
                # while all the cpu time is consumed.
                await asyncio.sleep(0)