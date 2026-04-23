def __init__(
      self,
      *,  # Makes all args keyword only.
      global_step: tf.Variable,
      trainer: Optional[runner.AbstractTrainer] = None,
      evaluator: Optional[runner.AbstractEvaluator] = None,
      strategy: Optional[tf.distribute.Strategy] = None,
      # Actions
      train_actions: Optional[Iterable[Action]] = None,
      eval_actions: Optional[Iterable[Action]] = None,
      # Train related
      steps_per_loop: Optional[Union[int, Callable[[int], int]]] = None,
      checkpoint_manager: Optional[tf.train.CheckpointManager] = None,
      enable_async_checkpointing: bool = False,
      # Summary related
      summary_interval: Optional[int] = None,
      summary_dir: Optional[str] = None,
      # Evaluation related
      eval_summary_dir: Optional[str] = None,
      summary_manager: Optional[utils.SummaryManagerInterface] = None,
      eval_summary_manager: Optional[utils.SummaryManagerInterface] = None):
    """Initializes a `Controller` instance.

    Note that if `checkpoint_manager` is provided and there are checkpoints in
    the associated model directory, the model will be restored from the most
    recent checkpoint during this `__init__` method.

    Args:
      global_step: An integer `tf.Variable` storing the global training step
        number. Usually this can be obtained from the `iterations` property of
        the model's optimizer (e.g. `trainer.optimizer.iterations`). In cases
        where multiple optimizers are used, or if one model "step" corresponds
        to more than one update to model parameters, users can create and
        increment their own global step variable as well. In this case it is
        recommended to create the `tf.Variable` inside the distribution strategy
        scope, with `aggregation=tf.VariableAggregation.ONLY_FIRST_REPLICA` (see
        also `orbit.utils.create_global_step()`).
      trainer: An instance of `orbit.AbstractTrainer`, which implements the
        inner training loop.
      evaluator: An instance of `orbit.AbstractEvaluator`, which implements
        evaluation.
      strategy: An instance of `tf.distribute.Strategy`. If not provided, the
        strategy will be initialized from the current in-scope strategy using
        `tf.distribute.get_strategy()`.
      train_actions: Optional `orbit.Action`s to call after each block of
        `steps_per_loop` training steps are run. These will be called with the
        output of `trainer.train`.
      eval_actions: Optional `orbit.Action`s to call after each evaluation.
        These will be called with the output of `evaluator.evaluate`.
      steps_per_loop: Optional integer to indicate the number of steps to run in
        each inner loop of training (passed as the `num_steps` parameter of
        `trainer.train`). It can be also a callable which takes the current
        global step value as input and returns the number of steps to run as
        output.
      checkpoint_manager: An instance of `tf.train.CheckpointManager`. If
        provided and there are checkpoints in the associated model directory,
        the model will be restored from the most recent checkpoint inside this
        `__init__` method. If not provided, the `Controller` will not
        automatically save to or restore from checkpoints.
      enable_async_checkpointing: Optional bool indicating whether to enable
        async checkpoint saving.
      summary_interval: Step interval for training summaries. Note that this
        argument only applies to `tf.summary` calls inside the `trainer.train`
        function. Summaries written by the `Controller` (specifically
        "steps_per_second" and output from the `trainer.train` method) will
        always be enabled unless the `summary_dir` parameter is `None`. If set,
        the value must be divisible by `steps_per_loop`.
      summary_dir: The directory to write summaries to. To use the same
        directory as for checkpointing, pass `checkpoint_manager.directory`. If
        `None`, no training summaries will be written.
      eval_summary_dir: The directory to write eval summaries to. If `None`, it
        will be set to `summary_dir`. If both `summary_dir` and
        `eval_summary_dir` are `None`, no eval summaries will be written.
      summary_manager: Instance of the summary manager. If set, the
        `summary_dir` will be ignored. Otherwise the summary manager will be
        created internally for TensorBoard summaries by default from the
        `summary_dir`.
      eval_summary_manager: Instance of the eval summary manager. If set, the
        `eval_summary_dir` will be ignored. Otherwise the eval summary manager
        will be created internally for TensorBoard summaries by default from the
        `eval_summary_dir`.

    Raises:
      ValueError: If both `trainer` and `evaluator` are `None`.
      ValueError: If `steps_per_loop` is not a positive integer or a callable.
      ValueError: If `summary_interval` is not a positive integer or is not
        divisible by `steps_per_loop`.
    """
    if trainer is None and evaluator is None:
      raise ValueError("`trainer` and `evaluator` should not both be `None`.")

    if trainer is not None:
      if steps_per_loop is None:
        raise ValueError(
            "`steps_per_loop` is required when `trainer` is provided.")
      elif not callable(steps_per_loop) and (
          not isinstance(steps_per_loop, int) or steps_per_loop < 1):
        raise ValueError(
            f"`steps_per_loop` ({steps_per_loop}) must be a positive integer "
            "or a callable.")

      if summary_interval is not None:
        if summary_interval <= 0:
          raise ValueError(
              f"`summary_interval` ({summary_interval}) must be larger than 0.")
        elif not callable(steps_per_loop) and (summary_interval % steps_per_loop
                                               != 0):
          raise ValueError(
              f"`summary interval` ({summary_interval}) must be a multiple "
              f"of `steps_per_loop` ({steps_per_loop}).")

    if not isinstance(global_step, tf.Variable):
      raise ValueError("`global_step` must be a `tf.Variable`.")

    self.trainer = trainer
    self.evaluator = evaluator

    self.strategy = strategy or tf.distribute.get_strategy()

    self.train_actions = () if train_actions is None else tuple(train_actions)
    self.eval_actions = () if eval_actions is None else tuple(eval_actions)

    self.global_step = global_step
    self.checkpoint_manager = checkpoint_manager
    self._enable_async_checkpoint_saving = enable_async_checkpointing
    self._checkpoint_options = tf.train.CheckpointOptions(
        enable_async=enable_async_checkpointing
    )

    if self.trainer is not None:
      self.step_timer = None
      self.summary_interval = summary_interval
      if summary_manager:
        self.summary_manager = summary_manager
      else:
        self.summary_manager = utils.SummaryManager(
            summary_dir, tf.summary.scalar, global_step=self.global_step)
      self._steps_per_loop = steps_per_loop

    if self.evaluator is not None:
      eval_summary_dir = eval_summary_dir or summary_dir
      if eval_summary_dir == summary_dir and self.trainer is not None:
        # Reuse the summary writer if train and evaluation summary directory
        # are the same.
        self.eval_summary_manager = self.summary_manager
      else:
        if eval_summary_manager:
          self.eval_summary_manager = eval_summary_manager
        else:
          self.eval_summary_manager = utils.SummaryManager(
              eval_summary_dir, tf.summary.scalar, global_step=self.global_step)

    tf.summary.experimental.set_step(self.global_step)

    # Restores the model if needed.
    if self.checkpoint_manager is not None:
      restored_path = self.restore_checkpoint()
      if restored_path:
        _log(f"restored from checkpoint: {restored_path}")

    # Set Orbit framework gauge to True value
    _orbit_api_gauge.get_cell().set(True)