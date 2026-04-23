def create_estimator_and_inputs(run_config,
                                hparams=None,
                                pipeline_config_path=None,
                                config_override=None,
                                train_steps=None,
                                sample_1_of_n_eval_examples=1,
                                sample_1_of_n_eval_on_train_examples=1,
                                model_fn_creator=create_model_fn,
                                use_tpu_estimator=False,
                                use_tpu=False,
                                num_shards=1,
                                params=None,
                                override_eval_num_epochs=True,
                                save_final_config=False,
                                postprocess_on_cpu=False,
                                export_to_tpu=None,
                                **kwargs):
  """Creates `Estimator`, input functions, and steps.

  Args:
    run_config: A `RunConfig`.
    hparams: (optional) A `HParams`.
    pipeline_config_path: A path to a pipeline config file.
    config_override: A pipeline_pb2.TrainEvalPipelineConfig text proto to
      override the config from `pipeline_config_path`.
    train_steps: Number of training steps. If None, the number of training steps
      is set from the `TrainConfig` proto.
    sample_1_of_n_eval_examples: Integer representing how often an eval example
      should be sampled. If 1, will sample all examples.
    sample_1_of_n_eval_on_train_examples: Similar to
      `sample_1_of_n_eval_examples`, except controls the sampling of training
      data for evaluation.
    model_fn_creator: A function that creates a `model_fn` for `Estimator`.
      Follows the signature:
      * Args:
        * `detection_model_fn`: Function that returns `DetectionModel` instance.
        * `configs`: Dictionary of pipeline config objects.
        * `hparams`: `HParams` object.
      * Returns: `model_fn` for `Estimator`.
    use_tpu_estimator: Whether a `TPUEstimator` should be returned. If False, an
      `Estimator` will be returned.
    use_tpu: Boolean, whether training and evaluation should run on TPU. Only
      used if `use_tpu_estimator` is True.
    num_shards: Number of shards (TPU cores). Only used if `use_tpu_estimator`
      is True.
    params: Parameter dictionary passed from the estimator. Only used if
      `use_tpu_estimator` is True.
    override_eval_num_epochs: Whether to overwrite the number of epochs to 1 for
      eval_input.
    save_final_config: Whether to save final config (obtained after applying
      overrides) to `estimator.model_dir`.
    postprocess_on_cpu: When use_tpu and postprocess_on_cpu are true,
      postprocess is scheduled on the host cpu.
    export_to_tpu: When use_tpu and export_to_tpu are true,
      `export_savedmodel()` exports a metagraph for serving on TPU besides the
      one on CPU.
    **kwargs: Additional keyword arguments for configuration override.

  Returns:
    A dictionary with the following fields:
    'estimator': An `Estimator` or `TPUEstimator`.
    'train_input_fn': A training input function.
    'eval_input_fns': A list of all evaluation input functions.
    'eval_input_names': A list of names for each evaluation input.
    'eval_on_train_input_fn': An evaluation-on-train input function.
    'predict_input_fn': A prediction input function.
    'train_steps': Number of training steps. Either directly from input or from
      configuration.
  """
  get_configs_from_pipeline_file = MODEL_BUILD_UTIL_MAP[
      'get_configs_from_pipeline_file']
  merge_external_params_with_configs = MODEL_BUILD_UTIL_MAP[
      'merge_external_params_with_configs']
  create_pipeline_proto_from_configs = MODEL_BUILD_UTIL_MAP[
      'create_pipeline_proto_from_configs']
  create_train_input_fn = MODEL_BUILD_UTIL_MAP['create_train_input_fn']
  create_eval_input_fn = MODEL_BUILD_UTIL_MAP['create_eval_input_fn']
  create_predict_input_fn = MODEL_BUILD_UTIL_MAP['create_predict_input_fn']
  detection_model_fn_base = MODEL_BUILD_UTIL_MAP['detection_model_fn_base']

  configs = get_configs_from_pipeline_file(
      pipeline_config_path, config_override=config_override)
  kwargs.update({
      'train_steps': train_steps,
      'use_bfloat16': configs['train_config'].use_bfloat16 and use_tpu
  })
  if sample_1_of_n_eval_examples >= 1:
    kwargs.update({'sample_1_of_n_eval_examples': sample_1_of_n_eval_examples})
  if override_eval_num_epochs:
    kwargs.update({'eval_num_epochs': 1})
    tf.logging.warning(
        'Forced number of epochs for all eval validations to be 1.')
  configs = merge_external_params_with_configs(
      configs, hparams, kwargs_dict=kwargs)
  model_config = configs['model']
  train_config = configs['train_config']
  train_input_config = configs['train_input_config']
  eval_config = configs['eval_config']
  eval_input_configs = configs['eval_input_configs']
  eval_on_train_input_config = copy.deepcopy(train_input_config)
  eval_on_train_input_config.sample_1_of_n_examples = (
      sample_1_of_n_eval_on_train_examples)
  if override_eval_num_epochs and eval_on_train_input_config.num_epochs != 1:
    tf.logging.warning('Expected number of evaluation epochs is 1, but '
                       'instead encountered `eval_on_train_input_config'
                       '.num_epochs` = '
                       '{}. Overwriting `num_epochs` to 1.'.format(
                           eval_on_train_input_config.num_epochs))
    eval_on_train_input_config.num_epochs = 1

  # update train_steps from config but only when non-zero value is provided
  if train_steps is None and train_config.num_steps != 0:
    train_steps = train_config.num_steps

  detection_model_fn = functools.partial(
      detection_model_fn_base, model_config=model_config)

  # Create the input functions for TRAIN/EVAL/PREDICT.
  train_input_fn = create_train_input_fn(
      train_config=train_config,
      train_input_config=train_input_config,
      model_config=model_config)
  eval_input_fns = []
  for eval_input_config in eval_input_configs:
    eval_input_fns.append(
        create_eval_input_fn(
            eval_config=eval_config,
            eval_input_config=eval_input_config,
            model_config=model_config))

  eval_input_names = [
      eval_input_config.name for eval_input_config in eval_input_configs
  ]
  eval_on_train_input_fn = create_eval_input_fn(
      eval_config=eval_config,
      eval_input_config=eval_on_train_input_config,
      model_config=model_config)
  predict_input_fn = create_predict_input_fn(
      model_config=model_config, predict_input_config=eval_input_configs[0])

  # Read export_to_tpu from hparams if not passed.
  if export_to_tpu is None and hparams is not None:
    export_to_tpu = hparams.get('export_to_tpu', False)
  tf.logging.info('create_estimator_and_inputs: use_tpu %s, export_to_tpu %s',
                  use_tpu, export_to_tpu)
  model_fn = model_fn_creator(detection_model_fn, configs, hparams, use_tpu,
                              postprocess_on_cpu)
  if use_tpu_estimator:
    estimator = tf_estimator.tpu.TPUEstimator(
        model_fn=model_fn,
        train_batch_size=train_config.batch_size,
        # For each core, only batch size 1 is supported for eval.
        eval_batch_size=num_shards * 1 if use_tpu else 1,
        use_tpu=use_tpu,
        config=run_config,
        export_to_tpu=export_to_tpu,
        eval_on_tpu=False,  # Eval runs on CPU, so disable eval on TPU
        params=params if params else {})
  else:
    estimator = tf_estimator.Estimator(model_fn=model_fn, config=run_config)

  # Write the as-run pipeline config to disk.
  if run_config.is_chief and save_final_config:
    pipeline_config_final = create_pipeline_proto_from_configs(configs)
    config_util.save_pipeline_config(pipeline_config_final, estimator.model_dir)

  return dict(
      estimator=estimator,
      train_input_fn=train_input_fn,
      eval_input_fns=eval_input_fns,
      eval_input_names=eval_input_names,
      eval_on_train_input_fn=eval_on_train_input_fn,
      predict_input_fn=predict_input_fn,
      train_steps=train_steps)