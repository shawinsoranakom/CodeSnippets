def run_experiment(
    *,
    distribution_strategy: tf.distribute.Strategy,
    task: multitask.MultiTask,
    model: base_model.MultiTaskBaseModel | tf_keras.Model,
    mode: str,
    params: configs.MultiTaskExperimentConfig,
    model_dir: str,
    run_post_eval: bool = False,
    trainer: base_trainer.MultiTaskBaseTrainer = None,
    eval_summary_manager: Optional[orbit.utils.SummaryManagerInterface] = None,
    best_ckpt_exporter_creator: Optional[Any] = train_utils
    .maybe_create_best_ckpt_exporter
) -> Union[base_model.MultiTaskBaseModel, Tuple[base_model.MultiTaskBaseModel,
                                                Mapping[Any, Any]]]:
  """Runs train/eval configured by the experiment params.

  Args:
    distribution_strategy: A distribution distribution_strategy.
    task: A MultiTaskTask instance.
    model: A MultiTaskBaseModel instance.
    mode: A 'str', specifying the mode. Can be 'train', 'eval', 'train_and_eval'
      or 'continuous_eval'.
    params: ExperimentConfig instance.
    model_dir: A 'str', a path to store model checkpoints and summaries.
    run_post_eval: Whether to run post eval once after training, metrics logs
      are returned.
    trainer: (optional) A multi-task trainer to use. If none is provided, a
      default one will be created based on `params`.
    eval_summary_manager: Instance of the eval summary manager. If set, the
      `eval_summary_dir` will be ignored. Otherwise the eval summary manager
      will be created internally for TensorBoard summaries by default from the
      `eval_summary_dir`.
    best_ckpt_exporter_creator: A functor for creating best checkpoint exporter.

  Returns:
      model: `base_model.MultiTaskBaseModel` instance.
  """

  is_training = 'train' in mode
  is_eval = 'eval' in mode
  with distribution_strategy.scope():
    if is_training and trainer is None:
      trainer = get_trainer(distribution_strategy, params, task, model)
    if is_eval:
      eval_steps = task.task_eval_steps
      evaluator = evaluator_lib.MultiTaskEvaluator(
          eval_tasks=task.tasks.values(),
          model=model,
          eval_steps=eval_steps,
          global_step=trainer.global_step if is_training else None,
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
      init_fn=model.initialize)

  controller = orbit.Controller(
      strategy=distribution_strategy,
      trainer=trainer,
      evaluator=evaluator,
      global_step=global_step,
      steps_per_loop=params.trainer.steps_per_loop,
      checkpoint_manager=checkpoint_manager,
      summary_dir=os.path.join(model_dir, 'train'),
      eval_summary_dir=os.path.join(model_dir, 'validation'),
      eval_summary_manager=eval_summary_manager,
      summary_interval=params.trainer.summary_interval)

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
      return model