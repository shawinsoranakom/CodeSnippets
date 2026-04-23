def evaluate(self, num_steps: tf.Tensor):
    """Performs evaluation for each `EvalTask`."""
    for metric in self.validation_losses.values():
      metric.reset_states()
    for metrics in self.validation_metrics.values():
      for metric in metrics:
        metric.reset_states()
    results = {}
    eval_iters = tf.nest.map_structure(iter, self.eval_datasets)

    for task in self.tasks:
      outputs = None
      name = task.name
      eval_iter = eval_iters[name]
      task_eval_steps = self.eval_steps.get(name, None) or num_steps
      outputs = self.task_fns[name](
          eval_iter,
          task_eval_steps,
          state=outputs,
          reduce_fn=task.aggregate_logs)
      task_metrics = self.validation_metrics[name]
      task_loss = self.validation_losses[name]
      logs = {}
      for metric in task_metrics + [task_loss]:
        logs[metric.name] = metric.result()
      if outputs:
        metrics = task.reduce_aggregated_logs(
            outputs, global_step=self.global_step)
        logs.update(metrics)
      results[name] = logs

    if self._checkpoint_exporter:
      self._checkpoint_exporter.maybe_export_checkpoint(
          self.checkpoint, results, self.global_step.numpy())
    return results