def main(_):
  gin.parse_config_files_and_bindings(FLAGS.gin_file, FLAGS.gin_params)
  params = train_utils.parse_configuration(FLAGS)
  model_dir = FLAGS.model_dir
  if 'train' in FLAGS.mode:
    # Pure eval modes do not output yaml files. Otherwise continuous eval job
    # may race against the train job for writing the same file.
    train_utils.serialize_config(params, model_dir)

  if 'train_and_eval' in FLAGS.mode:
    assert (params.task.train_data.feature_shape ==
            params.task.validation_data.feature_shape), (
                f'train {params.task.train_data.feature_shape} != validate '
                f'{params.task.validation_data.feature_shape}')

  if 'assemblenet' in FLAGS.experiment:
    if 'plus' in FLAGS.experiment:
      if 'eval' in FLAGS.mode:
        # Use the feature shape in validation_data for all jobs. The number of
        # frames in train_data will be used to construct the Assemblenet++
        # model.
        params.task.model.backbone.assemblenet_plus.num_frames = (
            params.task.validation_data.feature_shape[0])
        shape = params.task.validation_data.feature_shape
      else:
        params.task.model.backbone.assemblenet_plus.num_frames = (
            params.task.train_data.feature_shape[0])
        shape = params.task.train_data.feature_shape
      logging.info('mode %r num_frames %r feature shape %r', FLAGS.mode,
                   params.task.model.backbone.assemblenet_plus.num_frames,
                   shape)

    else:
      if 'eval' in FLAGS.mode:
        # Use the feature shape in validation_data for all jobs. The number of
        # frames in train_data will be used to construct the Assemblenet model.
        params.task.model.backbone.assemblenet.num_frames = (
            params.task.validation_data.feature_shape[0])
        shape = params.task.validation_data.feature_shape
      else:
        params.task.model.backbone.assemblenet.num_frames = (
            params.task.train_data.feature_shape[0])
        shape = params.task.train_data.feature_shape
      logging.info('mode %r num_frames %r feature shape %r', FLAGS.mode,
                   params.task.model.backbone.assemblenet.num_frames, shape)

  # Sets mixed_precision policy. Using 'mixed_float16' or 'mixed_bfloat16'
  # can have significant impact on model speeds by utilizing float16 in case of
  # GPUs, and bfloat16 in the case of TPUs. loss_scale takes effect only when
  # dtype is float16
  if params.runtime.mixed_precision_dtype:
    performance.set_mixed_precision_policy(params.runtime.mixed_precision_dtype)
  distribution_strategy = distribute_utils.get_distribution_strategy(
      distribution_strategy=params.runtime.distribution_strategy,
      all_reduce_alg=params.runtime.all_reduce_alg,
      num_gpus=params.runtime.num_gpus,
      tpu_address=params.runtime.tpu)
  with distribution_strategy.scope():
    task = task_factory.get_task(params.task, logging_dir=model_dir)

  train_lib.run_experiment(
      distribution_strategy=distribution_strategy,
      task=task,
      mode=FLAGS.mode,
      params=params,
      model_dir=model_dir)

  train_utils.save_gin_config(FLAGS.mode, model_dir)