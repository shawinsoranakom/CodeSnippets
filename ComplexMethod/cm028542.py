def create_dataset(file_paths,
                   batch_size,
                   params,
                   is_training=True,
                   input_pipeline_context=None):
  """Creates input dataset from (tf)records files for pretraining."""
  dataset = tf.data.Dataset.list_files(file_paths, shuffle=is_training)

  if input_pipeline_context and input_pipeline_context.num_input_pipelines > 1:
    if not is_training or params.input_sharding:
      dataset = dataset.shard(input_pipeline_context.num_input_pipelines,
                              input_pipeline_context.input_pipeline_id)

  if is_training:
    dataset = dataset.repeat()
    # We set shuffle buffer to exactly match total number of
    # training files to ensure that training data is well shuffled.
    dataset = dataset.shuffle(len(file_paths))

  # In parallel, create tf record dataset for each train files.
  # cycle_length = 8 means that up to 8 files will be read and deserialized in
  # parallel. You may want to increase this number if you have a large number of
  # CPU cores.
  dataset = dataset.interleave(
      tf.data.TFRecordDataset,
      cycle_length=8,
      num_parallel_calls=tf.data.experimental.AUTOTUNE)

  if is_training:
    dataset = dataset.shuffle(100)

  if params.get("multi_channel_cross_attention", value=False):
    dataset = process_multidoc_dataset(dataset, batch_size, params)
  else:
    if not params.input_data_not_padded:
      dataset = process_singledoc_dataset(dataset, batch_size, params)
    else:
      dataset = process_singledoc_transformer_dataset(dataset, batch_size,
                                                      params)
  dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)
  return dataset