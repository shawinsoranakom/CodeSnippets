def on_batch_end(self, batch, logs=None):
        if batch % 10 == 0:
            rows = {"loss": [logs["loss"]], "accuracy": [logs["accuracy"]]}
            self._epoch_chart.add_rows(rows)
        if batch % 100 == 99:
            rows = {"loss": [logs["loss"]], "accuracy": [logs["accuracy"]]}
            self._summary_chart.add_rows(rows)
        percent_complete = batch / self.params["steps"]
        self._epoch_progress.progress(math.ceil(percent_complete * 100))
        ts = time.time() - self._ts
        self._epoch_summary.text(
            "loss: %(loss)7.5f | accuracy: %(accuracy)7.5f | ts: %(ts)d"
            % {"loss": logs["loss"], "accuracy": logs["accuracy"], "ts": ts}
        )