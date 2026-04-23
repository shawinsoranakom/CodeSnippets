def __init__(
      self,
      config: ExperimentConfig,
      task: base_task.Task,
      model: tf_keras.Model,
      optimizer: tf.optimizers.Optimizer,
      train: bool = True,
      evaluate: bool = True,
      train_dataset: Optional[Union[tf.data.Dataset,
                                    tf.distribute.DistributedDataset]] = None,
      validation_dataset: Optional[Union[
          tf.data.Dataset, tf.distribute.DistributedDataset]] = None,
      checkpoint_exporter=None):
    """Initialize common trainer for TensorFlow models.

    Args:
      config: An `ExperimentConfig` instance specifying experiment config.
      task: A base_task.Task instance.
      model: The model instance, e.g. a tf_keras.Model instance.
      optimizer: tf.optimizers.Optimizer instance.
      train: bool, whether or not this trainer will be used for training.
        default to True.
      evaluate: bool, whether or not this trainer will be used for evaluation.
        default to True.
      train_dataset: a dataset object created for training. With tf.distribute,
        it needs to be a `DistributedDataset`.
      validation_dataset: a dataset object created for evaluation. With
        tf.distribute, it needs to be a `DistributedDataset`. The evaluator will
        create a dataset iterator for each eval round, so the dataset does not
        need to repeat.
      checkpoint_exporter: an object that has the `maybe_export_checkpoint`
        interface.
    """
    # Gets the current distribution strategy. If not inside any strategy scope,
    # it gets a single-replica no-op strategy.
    self._strategy = tf.distribute.get_strategy()
    self._validate_params(
        config,
        check_train_data=train_dataset is None,
        check_validation_data=validation_dataset is None)
    self._config = config
    self._task = task
    self._model = model
    self._optimizer = optimizer
    self._checkpoint_exporter = checkpoint_exporter
    self._recovery = None
    # Runtime options are only applied to train_step.
    # We use default for eval_step.
    self._runtime_options = get_runtime_options(config)

    # Creates a shadow copy of the weights to store weights moving average.
    if isinstance(self._optimizer, optimization.ExponentialMovingAverage
                 ) and not self._optimizer.has_shadow_copy:
      self._optimizer.shadow_copy(self._model)

    # global_step increases by 1 after each training iteration.
    # We should have global_step.numpy() == self.optimizer.iterations.numpy()
    # when there is only 1 optimizer.
    self._global_step = orbit.utils.create_global_step()
    if hasattr(self.model, "checkpoint_items"):
      checkpoint_items = self.model.checkpoint_items
    else:
      checkpoint_items = {}
    self._checkpoint = tf.train.Checkpoint(
        global_step=self.global_step,
        model=self.model,
        optimizer=self.optimizer,
        **checkpoint_items)

    self._train_loss = tf_keras.metrics.Mean("training_loss", dtype=tf.float32)
    self._validation_loss = tf_keras.metrics.Mean(
        "validation_loss", dtype=tf.float32)
    model_metrics = model.metrics if hasattr(model, "metrics") else []

    self.init_async()

    if train:
      self._train_metrics = self.task.build_metrics(
          training=True) + model_metrics
      train_dataset = train_dataset or self.distribute_dataset(
          self.task.build_inputs, self.config.task.train_data)
      orbit.StandardTrainer.__init__(
          self,
          train_dataset,
          options=orbit.StandardTrainerOptions(
              use_tf_while_loop=config.trainer.train_tf_while_loop,
              use_tf_function=config.trainer.train_tf_function,
              use_tpu_summary_optimization=config.trainer.allow_tpu_summary))

    if evaluate:
      self._validation_metrics = self.task.build_metrics(
          training=False) + model_metrics
      validation_dataset = validation_dataset or self.distribute_dataset(
          self.task.build_inputs, self.config.task.validation_data)
      orbit.StandardEvaluator.__init__(
          self,
          validation_dataset,
          options=orbit.StandardEvaluatorOptions(
              use_tf_function=config.trainer.eval_tf_function,
              use_tf_while_loop=config.trainer.eval_tf_while_loop))