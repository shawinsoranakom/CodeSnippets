def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        # Recompute first_column here since on_evaluate can be called before on_train_begin,
        # where it is normally initialized.
        self.first_column = "Epoch" if args.eval_strategy == IntervalStrategy.EPOCH else "Step"

        values = {"Training Loss": "No log", "Validation Loss": "No log"}
        for log in reversed(state.log_history):
            if "loss" in log:
                values["Training Loss"] = log["loss"]
                break

        if self.first_column == "Epoch":
            values["Epoch"] = int(state.epoch)
        else:
            values["Step"] = state.global_step
        if metrics is None:
            metrics = {}
        metric_key_prefix = "eval"
        for k in metrics:
            if k.endswith("_loss"):
                metric_key_prefix = re.sub(r"\_loss$", "", k)
        _ = metrics.pop("total_flos", None)
        _ = metrics.pop("epoch", None)
        _ = metrics.pop(f"{metric_key_prefix}_runtime", None)
        _ = metrics.pop(f"{metric_key_prefix}_samples_per_second", None)
        _ = metrics.pop(f"{metric_key_prefix}_steps_per_second", None)
        _ = metrics.pop(f"{metric_key_prefix}_model_preparation_time", None)

        for k, v in metrics.items():
            splits = k.split("_")
            name = " ".join([part.capitalize() for part in splits[1:]])
            if name == "Loss":
                # Single dataset
                name = "Validation Loss"
            values[name] = v

        if self.training_tracker is not None:
            tt = self.training_tracker
            tt.write_line(values)
            tt.remove_child()
            # Evaluation takes a long time so we should force the next update.
            self._force_next_update = True
        else:
            # No training tracker, but still show the metrics
            disp.display(disp.HTML(text_to_html_table([list(values.keys()), list(values.values())])))

        self.prediction_bar = None