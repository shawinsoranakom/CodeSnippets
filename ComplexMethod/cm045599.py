def _apply(
        self,
        table: pw.Table,
        key: pw.ColumnExpression,
        behavior: Behavior | None,
        instance: pw.ColumnExpression | None,
    ) -> pw.GroupedTable:
        check_joint_types(
            {
                "time_expr": (key, TimeEventType),
                "window.hop": (self.hop, IntervalType),
                "window.duration": (self.duration, IntervalType),
                "window.origin": (self.origin, TimeEventType),
            }
        )

        key_dtype = eval_type(key)
        assign_windows = self._window_assignment_function(key_dtype)

        target = table.with_columns(
            _pw_window=pw.udf(
                assign_windows,
                return_type=dt.List(
                    dt.Tuple(
                        eval_type(instance),  # type: ignore
                        key_dtype,
                        key_dtype,
                    )
                ),
                deterministic=True,
            )(instance, key),
            _pw_key=key,
        )
        target = target.flatten(target._pw_window, origin_id="_pw_original_id")
        target = target.with_columns(
            _pw_instance=pw.this._pw_window.get(0),
            _pw_window_start=pw.this._pw_window.get(1),
            _pw_window_end=pw.this._pw_window.get(2),
        )

        if behavior is not None:
            if isinstance(behavior, ExactlyOnceBehavior):
                duration: IntervalType
                # that is split in two if-s, as it helps mypy figure out proper types
                # one if impl left either self.ratio or self.duration as optionals
                # which won't fit into the duration variable of type IntervalType
                if self.duration is not None:
                    duration = self.duration
                elif self.ratio is not None:
                    duration = self.ratio * self.hop
                shift = (
                    behavior.shift
                    if behavior.shift is not None
                    else zero_length_interval(type(duration))
                )
                behavior = common_behavior(
                    duration + shift, shift, True  # type:ignore
                )
            elif not isinstance(behavior, CommonBehavior):
                raise ValueError(
                    f"behavior {behavior} unsupported in sliding/tumbling window"
                )

            if behavior.cutoff is not None:
                cutoff_threshold = pw.this._pw_window_end + behavior.cutoff
                target = target._freeze(cutoff_threshold, pw.this._pw_key)
            if behavior.delay is not None:
                target = target._buffer(
                    target._pw_window_start + behavior.delay, target._pw_key
                )
                target = target.with_columns(
                    _pw_key=pw.if_else(
                        target._pw_key > target._pw_window_start + behavior.delay,
                        target._pw_key,
                        target._pw_window_start + behavior.delay,
                    )
                )

            if behavior.cutoff is not None:
                cutoff_threshold = pw.this._pw_window_end + behavior.cutoff
                target = target._forget(
                    cutoff_threshold, pw.this._pw_key, behavior.keep_results
                )

        filter_out_results_of_forgetting = (
            behavior is not None
            and behavior.cutoff is not None
            and behavior.keep_results
        )

        target = target.groupby(
            target._pw_window,
            target._pw_window_start,
            target._pw_window_end,
            pw.this._pw_instance,
            instance=target._pw_instance if instance is not None else None,
            _filter_out_results_of_forgetting=filter_out_results_of_forgetting,
            _is_window=True,
        )

        return target