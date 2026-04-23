def data_generator(self, epochs_between_evals):
    """Yields examples during local training."""
    assert not self._stream_files
    assert self._is_training or epochs_between_evals == 1

    if self._is_training:
      for _ in range(self._batches_per_epoch * epochs_between_evals):
        yield self._result_queue.get(timeout=300)

    else:
      if self._result_reuse:
        assert len(self._result_reuse) == self._batches_per_epoch

        for i in self._result_reuse:
          yield i
      else:
        # First epoch.
        for _ in range(self._batches_per_epoch * epochs_between_evals):
          result = self._result_queue.get(timeout=300)
          self._result_reuse.append(result)
          yield result