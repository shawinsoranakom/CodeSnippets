def on_log(self, args, state, control, model=None, processing_class=None, logs=None, **kwargs):
        if self._clearml is None:
            return
        if not self._initialized:
            self.setup(args, state, model, processing_class, **kwargs)
        if state.is_world_process_zero:
            eval_prefix = "eval_"
            eval_prefix_len = len(eval_prefix)
            test_prefix = "test_"
            test_prefix_len = len(test_prefix)
            single_value_scalars = [
                "train_runtime",
                "train_samples_per_second",
                "train_steps_per_second",
                "train_loss",
                "total_flos",
                "epoch",
            ]
            for k, v in logs.items():
                if isinstance(v, (int, float)):
                    if k in single_value_scalars:
                        self._clearml_task.get_logger().report_single_value(
                            name=k + ClearMLCallback.log_suffix, value=v
                        )
                    elif k.startswith(eval_prefix):
                        self._clearml_task.get_logger().report_scalar(
                            title="eval" + ClearMLCallback.log_suffix,
                            series=k[eval_prefix_len:],
                            value=v,
                            iteration=state.global_step,
                        )
                    elif k.startswith(test_prefix):
                        self._clearml_task.get_logger().report_scalar(
                            title="test" + ClearMLCallback.log_suffix,
                            series=k[test_prefix_len:],
                            value=v,
                            iteration=state.global_step,
                        )
                    else:
                        self._clearml_task.get_logger().report_scalar(
                            title="train" + ClearMLCallback.log_suffix,
                            series=k,
                            value=v,
                            iteration=state.global_step,
                        )
                else:
                    logger.warning(
                        "Trainer is attempting to log a value of "
                        f'"{v}" of type {type(v)} for key "{k}" as a scalar. '
                        "This invocation of ClearML logger's  report_scalar() "
                        "is incorrect so we dropped this attribute."
                    )