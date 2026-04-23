def as_result_dict(self, *, for_callback: bool = False, for_round_trip: bool = False, censor_callback_result: bool = False) -> dict[str, object]:
        result: dict[str, t.Any] = {
            self._result_key_magic(result_key): value
            for field_name, result_key in self._get_field_name_to_result_key_mapping(for_callback=for_callback, for_round_trip=for_round_trip).items()
            if (value := getattr(self, field_name)) is not None
        }

        result.update(self.result_data)

        # RPFIX-5: IMPL: is this where we want stdout/stderr handling?
        # pre-split stdout/stderr into lines if needed

        if 'stdout' in result and 'stdout_lines' not in result:
            # if the value is 'False', a default won't catch it.
            txt = result.get('stdout', None) or ''
            result.update(stdout_lines=txt.splitlines())

        if 'stderr' in result and 'stderr_lines' not in result:
            # if the value is 'False', a default won't catch it.
            txt = result.get('stderr', None) or ''
            result.update(stderr_lines=txt.splitlines())

        if for_callback:
            if censor_callback_result:
                result = {key: value for key in PRESERVE if (value := result.get(key, ...)) is not ...}
                result.update(censored="the output has been hidden due to the fact that 'no_log: true' was specified for this result")

        if self.loop_results is not None:
            # loop results need to be added after censor_result on the outer result since it's currently naive about whether it's looking at a loop item or not
            result.update(
                results=[
                    loop_result.as_result_dict(
                        for_callback=for_callback,
                        for_round_trip=for_round_trip,
                        censor_callback_result=censor_callback_result or loop_result.no_log,
                    )
                    for loop_result in self.loop_results
                ]
            )

        if for_callback:
            result = _vars.transform_to_native_types(result)

        return result