def run_experiment_with_multitask_eval(
    *,
    distribution_strategy: tf.distribute.Strategy,
    train_task: base_task.Task,
    eval_tasks: List[base_task.Task],
    mode: str,
    params: configs.MultiEvalExperimentConfig,
    model_dir: str,
    run_post_eval: bool = False,
    save_summary: bool = True,
    trainer: Optional[core_lib.Trainer] = None,
    eval_summary_manager: Optional[orbit.utils.SummaryManagerInterface] = None,
    best_ckpt_exporter_creator: Optional[Any] = train_utils
    .maybe_create_best_ckpt_exporter,
    train_actions_factory: Optional[TrainActionsFactoryType] = None,
    eval_actions_factory: Optional[EvalActionsFactoryType] = None,
) -> Tuple[Any, Any]:
  """Runs train/eval configured by the experiment params.

  Args:
    distribution_strategy: A distribution distribution_strategy.
    train_task: A base_task.Task instance.
    eval_tasks: A list of evaluation tasks.
    mode: A 'str', specifying the mode. Can be 'train', 'eval', 'train_and_eval'
      or 'continuous_eval'.
    params: MultiEvalExperimentConfig instance.
    model_dir: A 'str', a path to store model checkpoints and summaries.
    run_post_eval: Whether to run post eval once after training, metrics logs
      are returned.
    save_summary: Whether to save train and validation summary.
    trainer: the core_lib.Trainer instance. It should be created within the
      strategy.scope(). If not provided, an instance will be created by default
      if `mode` contains 'train'.
    eval_summary_manager: Instance of the eval summary manager. If set, the
      `eval_summary_dir` will be ignored. Otherwise the eval summary manager
      will be created internally for TensorBoard summaries by default from the
      `eval_summary_dir`.
    best_ckpt_exporter_creator: A functor for creating best checkpoint exporter.
    train_actions_factory: Optional factory function to create train actions.
    eval_actions_factory: Optional factory function to create eval actions.

  Returns:
      model: `tf_keras.Model` instance.
  """

  is_training = 'train' in mode
  is_eval = 'eval' in mode
  with distribution_strategy.scope():
    if is_training:
      trainer = trainer or core_lib.Trainer(
          config=params,
          task=train_task,
          model=train_task.build_model(),
          optimizer=train_utils.create_optimizer(train_task, params),
          train=True,
          evaluate=False)
    else:
      trainer = None

    # Build the model or fetch the pre-cached one (which could be either
    # multi-task model or single task model).
    if trainer is None:
      if isinstance(train_task, multitask.MultiTask):
        model = train_task.build_multitask_model()
      else:
        model = train_task.build_model()
    else:
      if isinstance(trainer, base_trainer.MultiTaskBaseTrainer):
        model = trainer.multi_task_model
      else:
        model = trainer.model

    if is_eval:
      eval_steps = dict([(task_routine.task_config.name,
                          task_routine.eval_steps)
                         for task_routine in params.eval_tasks])
      evaluator = evaluator_lib.MultiTaskEvaluator(
          eval_tasks=eval_tasks,
          model=model,
          global_step=trainer.global_step if is_training else None,
          eval_steps=eval_steps,
          checkpoint_exporter=best_ckpt_exporter_creator(params, model_dir))
    else:
      evaluator = None

  if trainer:
    checkpoint = trainer.checkpoint
    global_step = trainer.global_step
  else:
    checkpoint = evaluator.checkpoint
    global_step = evaluator.global_step

  checkpoint_manager = tf.train.CheckpointManager(
      checkpoint,
      directory=model_dir,
      max_to_keep=params.trainer.max_to_keep,
      step_counter=global_step,
      checkpoint_interval=params.trainer.checkpoint_interval,
      init_fn=trainer.initialize if trainer else None)

  if trainer and train_actions_factory:
    # pytype: disable=wrong-keyword-args
    train_actions = train_actions_factory(
        params=params,
        trainer=trainer,
        model_dir=model_dir,
        checkpoint_manager=checkpoint_manager,
    )
    # pytype: enable=wrong-keyword-args
  else:
    train_actions = None

  if evaluator and eval_actions_factory:
    eval_actions = eval_actions_factory(params, evaluator, model_dir)
  else:
    eval_actions = None

  controller = orbit.Controller(
      strategy=distribution_strategy,
      trainer=trainer,
      evaluator=evaluator,
      global_step=global_step,
      steps_per_loop=params.trainer.steps_per_loop,
      checkpoint_manager=checkpoint_manager,
      summary_dir=os.path.join(model_dir, 'train') if save_summary else None,
      eval_summary_dir=os.path.join(model_dir, 'validation') if
      (save_summary) else None,
      eval_summary_manager=eval_summary_manager,
      summary_interval=params.trainer.summary_interval if
      (save_summary) else None,
      train_actions=train_actions,
      eval_actions=eval_actions,
      )

  logging.info('Starts to execute mode: %s', mode)
  with distribution_strategy.scope():
    if mode == 'train':
      controller.train(steps=params.trainer.train_steps)
    elif mode == 'train_and_eval':
      controller.train_and_evaluate(
          train_steps=params.trainer.train_steps,
          eval_steps=params.trainer.validation_steps,
          eval_interval=params.trainer.validation_interval)
    elif mode == 'eval':
      controller.evaluate(steps=params.trainer.validation_steps)
    elif mode == 'continuous_eval':

      def timeout_fn():
        if evaluator.global_step.numpy() >= params.trainer.train_steps:
          return True
        return False

      controller.evaluate_continuously(
          steps=params.trainer.validation_steps,
          timeout=params.trainer.continuous_eval_timeout,
          timeout_fn=timeout_fn)
    else:
      raise NotImplementedError('The mode is not implemented: %s' % mode)

    if run_post_eval:
      return model, evaluator.evaluate(
          tf.convert_to_tensor(params.trainer.validation_steps))  # pytype: disable=bad-return-type  # typed-keras
    else:
      return model, {}