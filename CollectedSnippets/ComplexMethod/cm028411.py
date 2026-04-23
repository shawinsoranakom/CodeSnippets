def result(self) -> dict[str, tf.Tensor]:
    """Aggregates all the metrics' results into a flattened dictionary."""
    metric_name = self._metric.name
    metric_result = self._metric.result()
    slice_results = [metric.result() for metric in self._sliced_metrics]

    if isinstance(metric_result, tf.Tensor):
      results = {metric_name: metric_result}
      slice_names = (f"{metric_name}/{name}" for name in self._slice_names)
      results.update(zip(slice_names, slice_results))
      return results

    if isinstance(metric_result, dict) and all(
        isinstance(result, tf.Tensor) for result in metric_result.values()
    ):
      results = {**metric_result}
      for slice_name, slice_result in zip(self._slice_names, slice_results):
        result_names, result_values = zip(*slice_result.items())
        slice_names = [f"{name}/{slice_name}" for name in result_names]
        results.update(zip(slice_names, result_values))
      return results

    raise ValueError(
        "The output of the given metric must either be a `tf.Tensor` or "
        "a `dict[str, tf.Tensor]`, but got unsupported output: "
        f"{metric_result}."
    )