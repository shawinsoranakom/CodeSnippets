def run(callbacks=None):
  """Runs the experiment."""
  keras_utils.set_session_config(enable_xla=FLAGS.enable_xla)

  params = config_factory.config_generator(FLAGS.model)

  params = params_dict.override_params_dict(
      params, FLAGS.config_file, is_strict=True)

  params = params_dict.override_params_dict(
      params, FLAGS.params_override, is_strict=True)
  params.override(
      {
          'strategy_type': FLAGS.strategy_type,
          'model_dir': FLAGS.model_dir,
          'strategy_config': executor.strategy_flags_dict(),
      },
      is_strict=False)

  # Make sure use_tpu and strategy_type are in sync.
  params.use_tpu = (params.strategy_type == 'tpu')

  if not params.use_tpu:
    params.override({
        'architecture': {
            'use_bfloat16': False,
        },
        'norm_activation': {
            'use_sync_bn': False,
        },
    }, is_strict=True)

  params.validate()
  params.lock()
  pp = pprint.PrettyPrinter()
  params_str = pp.pformat(params.as_dict())
  logging.info('Model Parameters: %s', params_str)

  train_input_fn = None
  eval_input_fn = None
  training_file_pattern = FLAGS.training_file_pattern or params.train.train_file_pattern
  eval_file_pattern = FLAGS.eval_file_pattern or params.eval.eval_file_pattern
  if not training_file_pattern and not eval_file_pattern:
    raise ValueError('Must provide at least one of training_file_pattern and '
                     'eval_file_pattern.')

  if training_file_pattern:
    # Use global batch size for single host.
    train_input_fn = input_reader.InputFn(
        file_pattern=training_file_pattern,
        params=params,
        mode=input_reader.ModeKeys.TRAIN,
        batch_size=params.train.batch_size)

  if eval_file_pattern:
    eval_input_fn = input_reader.InputFn(
        file_pattern=eval_file_pattern,
        params=params,
        mode=input_reader.ModeKeys.PREDICT_WITH_GT,
        batch_size=params.eval.batch_size,
        num_examples=params.eval.eval_samples)

  if callbacks is None:
    callbacks = []

  if FLAGS.log_steps:
    callbacks.append(
        keras_utils.TimeHistory(
            batch_size=params.train.batch_size,
            log_steps=FLAGS.log_steps,
        ))

  return run_executor(
      params,
      FLAGS.mode,
      checkpoint_path=FLAGS.checkpoint_path,
      train_input_fn=train_input_fn,
      eval_input_fn=eval_input_fn,
      callbacks=callbacks)