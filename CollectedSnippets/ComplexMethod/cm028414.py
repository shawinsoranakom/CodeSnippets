def __call__(self, ctx: tf.distribute.InputContext) -> tf.data.Dataset:
    params = self._params
    # Per replica batch size.
    batch_size = ctx.get_per_replica_batch_size(
        params.global_batch_size) if ctx else params.global_batch_size
    if self._use_synthetic_data:
      return self._generate_synthetic_data(ctx, batch_size)

    @tf.function
    def _parse_fn(example: tf.Tensor):
      """Parser function for pre-processed Criteo TSV records."""
      label_defaults = [[0.0]]
      dense_defaults = [
          [0.0] for _ in range(self._num_dense_features)
      ]
      num_sparse_features = len(self._vocab_sizes)
      categorical_defaults = [
          [0] for _ in range(num_sparse_features)
      ]
      record_defaults = label_defaults + dense_defaults + categorical_defaults
      fields = tf.io.decode_csv(
          example, record_defaults, field_delim='\t', na_value='-1')

      num_labels = 1
      label = tf.reshape(fields[0], [batch_size, 1])

      features = {}
      num_dense = len(dense_defaults)

      dense_features = []
      offset = num_labels
      for idx in range(num_dense):
        dense_features.append(fields[idx + offset])
      features['dense_features'] = tf.stack(dense_features, axis=1)

      offset += num_dense
      features['sparse_features'] = {}

      sparse_tensors = []
      for idx, (vocab_size, multi_hot_size) in enumerate(
          zip(self._vocab_sizes, self._multi_hot_sizes)
      ):
        sparse_tensor = tf.reshape(fields[idx + offset], [batch_size, 1])
        sparse_tensor_synthetic = tf.random.uniform(
            shape=(batch_size, multi_hot_size - 1),
            maxval=int(vocab_size),
            dtype=tf.int32,
        )
        sparse_tensors.append(
            tf.sparse.from_dense(
                tf.concat([sparse_tensor, sparse_tensor_synthetic], axis=1)
            )
        )

      sparse_tensor_elements = {
          str(i): sparse_tensors[i] for i in range(len(sparse_tensors))
      }

      features['sparse_features'] = sparse_tensor_elements

      return features, label

    filenames = tf.data.Dataset.list_files(self._file_pattern, shuffle=False)

    # Shard the full dataset according to host number.
    # Each host will get 1 / num_of_hosts portion of the data.
    if params.sharding and ctx and ctx.num_input_pipelines > 1:
      filenames = filenames.shard(ctx.num_input_pipelines,
                                  ctx.input_pipeline_id)

    num_shards_per_host = 1
    if params.sharding:
      num_shards_per_host = params.num_shards_per_host

    def make_dataset(shard_index):
      filenames_for_shard = filenames.shard(num_shards_per_host, shard_index)
      dataset = tf.data.TextLineDataset(filenames_for_shard)
      if params.is_training:
        dataset = dataset.repeat()
      dataset = dataset.batch(batch_size, drop_remainder=True)
      dataset = dataset.map(_parse_fn,
                            num_parallel_calls=tf.data.experimental.AUTOTUNE)
      return dataset

    indices = tf.data.Dataset.range(num_shards_per_host)
    dataset = indices.interleave(
        map_func=make_dataset,
        cycle_length=params.cycle_length,
        num_parallel_calls=tf.data.experimental.AUTOTUNE)

    dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)
    if self._params.use_cached_data:
      dataset = dataset.take(1).cache().repeat()

    return dataset