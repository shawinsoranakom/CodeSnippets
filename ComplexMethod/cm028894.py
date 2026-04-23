def evaluate(self, num_steps: tf.Tensor) -> Optional[runner.Output]:
    """Implements `num_steps` steps of evaluation.

    Args:
      num_steps: The number of evaluation steps to run. When this is -1,
        evaluation proceeds until a call to `eval_step` raises a `StopIteration`
        or `tf.errors.OutOfRangeError`.

    Returns:
      The output of `self.eval_end()`.

    Raises:
      ValueError: If `options.use_tf_while_loop` is `True` and `num_steps` is
        unspecified.
    """
    if self._eval_options.use_tf_while_loop and num_steps == -1:
      raise ValueError("Looping until exhausted is not supported if "
                       "`options.use_tf_while_loop` is `True`")

    outputs = self.eval_begin()  # pylint: disable=assignment-from-no-return

    has_state = outputs is not None
    if self._eval_loop_fn is None:
      self._eval_loop_fn = self.create_eval_loop_fn(has_state)

    # If `recreate_iterator_for_each_eval` is `True`, `self._eval_iter` is
    # always None.
    if self._eval_iter is None:
      eval_iter = tf.nest.map_structure(iter, self.eval_dataset)
      if not self._eval_options.recreate_iterator_for_each_eval:
        self._eval_iter = eval_iter
    else:
      eval_iter = self._eval_iter

    if self._eval_options.use_tf_while_loop and not has_state:
      self._eval_loop_fn(eval_iter, num_steps)
    else:
      outputs = self._eval_loop_fn(
          eval_iter, num_steps, state=outputs, reduce_fn=self.eval_reduce)

    if outputs is None:
      return self.eval_end()
    else:
      return self.eval_end(outputs)