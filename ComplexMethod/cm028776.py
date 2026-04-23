def predict(task: SentencePredictionTask,
            params: cfg.DataConfig,
            model: tf_keras.Model,
            params_aug: Optional[cfg.DataConfig] = None,
            test_time_aug_wgt: float = 0.3) -> List[Union[int, float]]:
  """Predicts on the input data.

  Args:
    task: A `SentencePredictionTask` object.
    params: A `cfg.DataConfig` object.
    model: A keras.Model.
    params_aug: A `cfg.DataConfig` object for augmented data.
    test_time_aug_wgt: Test time augmentation weight. The prediction score will
      use (1. - test_time_aug_wgt) original prediction plus test_time_aug_wgt
      augmented prediction.

  Returns:
    A list of predictions with length of `num_examples`. For regression task,
      each element in the list is the predicted score; for classification task,
      each element is the predicted class id.
  """

  def predict_step(inputs):
    """Replicated prediction calculation."""
    x = inputs
    example_id = x.pop('example_id')
    outputs = task.inference_step(x, model)
    return dict(example_id=example_id, predictions=outputs)

  def aggregate_fn(state, outputs):
    """Concatenates model's outputs."""
    if state is None:
      state = []

    for per_replica_example_id, per_replica_batch_predictions in zip(
        outputs['example_id'], outputs['predictions']):
      state.extend(zip(per_replica_example_id, per_replica_batch_predictions))
    return state

  dataset = orbit.utils.make_distributed_dataset(tf.distribute.get_strategy(),
                                                 task.build_inputs, params)
  outputs = utils.predict(predict_step, aggregate_fn, dataset)

  # When running on TPU POD, the order of output cannot be maintained,
  # so we need to sort by example_id.
  outputs = sorted(outputs, key=lambda x: x[0])
  is_regression = task.task_config.model.num_classes == 1
  if params_aug is not None:
    dataset_aug = orbit.utils.make_distributed_dataset(
        tf.distribute.get_strategy(), task.build_inputs, params_aug)
    outputs_aug = utils.predict(predict_step, aggregate_fn, dataset_aug)
    outputs_aug = sorted(outputs_aug, key=lambda x: x[0])
    if is_regression:
      return [(1. - test_time_aug_wgt) * x[1] + test_time_aug_wgt * y[1]
              for x, y in zip(outputs, outputs_aug)]
    else:
      return [
          tf.argmax(
              (1. - test_time_aug_wgt) * x[1] + test_time_aug_wgt * y[1],
              axis=-1) for x, y in zip(outputs, outputs_aug)
      ]
  if is_regression:
    return [x[1] for x in outputs]
  else:
    return [tf.argmax(x[1], axis=-1) for x in outputs]