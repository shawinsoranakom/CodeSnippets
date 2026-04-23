def on_train_batch_end(self, batch, logs=None):
        if self._should_write_train_graph:
            self._write_keras_model_train_graph()
            self._should_write_train_graph = False
        if self.write_steps_per_second:
            batch_run_time = time.time() - self._batch_start_time
            self.summary.scalar(
                "batch_steps_per_second",
                1.0 / batch_run_time,
                step=self._global_train_batch,
            )

        # `logs` isn't necessarily always a dict
        if isinstance(logs, dict):
            for name, value in logs.items():
                self.summary.scalar(
                    f"batch_{name}", value, step=self._global_train_batch
                )

        if not self._should_trace:
            return

        if self._is_tracing:
            if self._profiler_started and self._batch_trace_context is not None:
                backend.tensorboard.stop_batch_trace(self._batch_trace_context)
                self._batch_trace_context = None
            if self._global_train_batch >= self._stop_batch:
                self._stop_trace()