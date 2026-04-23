def create_ncf_input_data(params,
                          producer=None,
                          input_meta_data=None,
                          strategy=None):
  """Creates NCF training/evaluation dataset.

  Args:
    params: Dictionary containing parameters for train/evaluation data.
    producer: Instance of BaseDataConstructor that generates data online. Must
      not be None when params['train_dataset_path'] or
      params['eval_dataset_path'] is not specified.
    input_meta_data: A dictionary of input metadata to be used when reading data
      from tf record files. Must be specified when params["train_input_dataset"]
      is specified.
    strategy: Distribution strategy used for distributed training. If specified,
      used to assert that evaluation batch size is correctly a multiple of total
      number of devices used.

  Returns:
    (training dataset, evaluation dataset, train steps per epoch,
    eval steps per epoch)

  Raises:
    ValueError: If data is being generated online for when using TPU's.
  """
  # NCF evaluation metric calculation logic assumes that evaluation data
  # sample size are in multiples of (1 + number of negative samples in
  # evaluation) for each device. As so, evaluation batch size must be a
  # multiple of (number of replicas * (1 + number of negative samples)).
  num_devices = strategy.num_replicas_in_sync if strategy else 1
  if (params["eval_batch_size"] % (num_devices *
                                   (1 + rconst.NUM_EVAL_NEGATIVES))):
    raise ValueError("Evaluation batch size must be divisible by {} "
                     "times {}".format(num_devices,
                                       (1 + rconst.NUM_EVAL_NEGATIVES)))

  if params["train_dataset_path"]:
    assert params["eval_dataset_path"]

    train_dataset = create_dataset_from_tf_record_files(
        params["train_dataset_path"],
        input_meta_data["train_prebatch_size"],
        params["batch_size"],
        is_training=True,
        rebatch=False)

    # Re-batch evaluation dataset for TPU Pods.
    # TODO (b/162341937) remove once it's fixed.
    eval_rebatch = (params["use_tpu"] and strategy.num_replicas_in_sync > 8)
    eval_dataset = create_dataset_from_tf_record_files(
        params["eval_dataset_path"],
        input_meta_data["eval_prebatch_size"],
        params["eval_batch_size"],
        is_training=False,
        rebatch=eval_rebatch)

    num_train_steps = int(input_meta_data["num_train_steps"])
    num_eval_steps = int(input_meta_data["num_eval_steps"])
  else:
    if params["use_tpu"]:
      raise ValueError("TPU training does not support data producer yet. "
                       "Use pre-processed data.")

    assert producer
    # Start retrieving data from producer.
    train_dataset, eval_dataset = create_dataset_from_data_producer(
        producer, params)
    num_train_steps = producer.train_batches_per_epoch
    num_eval_steps = producer.eval_batches_per_epoch

  return train_dataset, eval_dataset, num_train_steps, num_eval_steps