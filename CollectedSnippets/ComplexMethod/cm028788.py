def main(_):
  gin.parse_config_files_and_bindings(FLAGS.gin_file, FLAGS.gin_params)
  params = train_utils.parse_configuration(FLAGS)
  model_dir = FLAGS.model_dir
  if 'train' in FLAGS.mode:
    # Pure eval modes do not output yaml files. Otherwise continuous eval job
    # may race against the train job for writing the same file.
    train_utils.serialize_config(params, model_dir)

  # Sets mixed_precision policy. Using 'mixed_float16' or 'mixed_bfloat16'
  # can have significant impact on model speeds by utilizing float16 in case of
  # GPUs, and bfloat16 in the case of TPUs. loss_scale takes effect only when
  # dtype is float16
  if params.runtime.mixed_precision_dtype:
    performance.set_mixed_precision_policy(params.runtime.mixed_precision_dtype)

  input_partition_dims = None
  if FLAGS.mode == 'train_and_eval':
    if np.prod(params.task.train_input_partition_dims) != np.prod(
        params.task.eval_input_partition_dims):
      raise ValueError('Train and eval input partition dims can not be'
                       'partitioned on the same node')
    else:
      input_partition_dims = get_computation_shape_for_model_parallelism(
          params.task.train_input_partition_dims)
  elif FLAGS.mode == 'train':
    if params.task.train_input_partition_dims:
      input_partition_dims = get_computation_shape_for_model_parallelism(
          params.task.train_input_partition_dims)
  elif FLAGS.mode == 'eval' or FLAGS.mode == 'continuous_eval':
    if params.task.eval_input_partition_dims:
      input_partition_dims = get_computation_shape_for_model_parallelism(
          params.task.eval_input_partition_dims)

  distribution_strategy = create_distribution_strategy(
      distribution_strategy=params.runtime.distribution_strategy,
      num_gpus=params.runtime.num_gpus,
      input_partition_dims=input_partition_dims,
      tpu_address=params.runtime.tpu)
  with distribution_strategy.scope():
    task = task_factory.get_task(params.task, logging_dir=model_dir)

  train_lib.run_experiment(
      distribution_strategy=distribution_strategy,
      task=task,
      mode=FLAGS.mode,
      params=params,
      model_dir=model_dir)