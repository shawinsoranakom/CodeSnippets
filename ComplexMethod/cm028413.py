def _get_tpu_embedding_feature_config(
    vocab_sizes: List[int],
    embedding_dim: Union[int, List[int]],
    table_name_prefix: str = 'embedding_table',
    batch_size: Optional[int] = None,
    max_ids_per_chip_per_sample: Optional[int] = None,
    max_ids_per_table: Optional[Union[int, List[int]]] = None,
    max_unique_ids_per_table: Optional[Union[int, List[int]]] = None,
    allow_id_dropping: bool = False,
    initialize_tables_on_host: bool = False,
) -> Tuple[
    Dict[str, tf.tpu.experimental.embedding.FeatureConfig],
    Optional[tf.tpu.experimental.embedding.SparseCoreEmbeddingConfig],
]:
  """Returns TPU embedding feature config.

  i'th table config will have vocab size of vocab_sizes[i] and embedding
  dimension of embedding_dim if embedding_dim is an int or embedding_dim[i] if
  embedding_dim is a list).
  Args:
    vocab_sizes: List of sizes of categories/id's in the table.
    embedding_dim: An integer or a list of embedding table dimensions.
    table_name_prefix: a prefix for embedding tables.
    batch_size: Per-replica batch size.
    max_ids_per_chip_per_sample: Maximum number of embedding ids per chip per
      sample.
    max_ids_per_table: Maximum number of embedding ids per table.
    max_unique_ids_per_table: Maximum number of unique embedding ids per table.
    allow_id_dropping: bool to allow id dropping.
    initialize_tables_on_host: bool : if the embedding table size is more than 
      what HBM can handle, this flag will help initialize the full embedding
      tables on host and then copy shards to HBM.

  Returns:
    A dictionary of feature_name, FeatureConfig pairs.
  """
  if isinstance(embedding_dim, List):
    if len(vocab_sizes) != len(embedding_dim):
      raise ValueError(
          f'length of vocab_sizes: {len(vocab_sizes)} is not equal to the '
          f'length of embedding_dim: {len(embedding_dim)}'
      )
  elif isinstance(embedding_dim, int):
    embedding_dim = [embedding_dim] * len(vocab_sizes)
  else:
    raise ValueError(
        'embedding_dim is not either a list or an int, got '
        f'{type(embedding_dim)}'
    )

  if isinstance(max_ids_per_table, List):
    if len(vocab_sizes) != len(max_ids_per_table):
      raise ValueError(
          f'length of vocab_sizes: {len(vocab_sizes)} is not equal to the '
          f'length of max_ids_per_table: {len(max_ids_per_table)}'
      )
  elif isinstance(max_ids_per_table, int):
    max_ids_per_table = [max_ids_per_table] * len(vocab_sizes)
  elif max_ids_per_table is not None:
    raise ValueError(
        'max_ids_per_table is not either a list or an int or None, got '
        f'{type(max_ids_per_table)}'
    )

  if isinstance(max_unique_ids_per_table, List):
    if len(vocab_sizes) != len(max_unique_ids_per_table):
      raise ValueError(
          f'length of vocab_sizes: {len(vocab_sizes)} is not equal to the '
          'length of max_unique_ids_per_table: '
          f'{len(max_unique_ids_per_table)}'
      )
  elif isinstance(max_unique_ids_per_table, int):
    max_unique_ids_per_table = [max_unique_ids_per_table] * len(vocab_sizes)
  elif max_unique_ids_per_table is not None:
    raise ValueError(
        'max_unique_ids_per_table is not either a list or an int or None, '
        f'got {type(max_unique_ids_per_table)}'
    )

  feature_config = {}
  sparsecore_config = None
  max_ids_per_table_dict = {}
  max_unique_ids_per_table_dict = {}

  for i, vocab_size in enumerate(vocab_sizes):
    table_config = tf.tpu.experimental.embedding.TableConfig(
        vocabulary_size=vocab_size,
        dim=embedding_dim[i],
        combiner='mean',
        initializer=tf.initializers.TruncatedNormal(
            mean=0.0, stddev=1 / math.sqrt(embedding_dim[i])
        ),
        name=table_name_prefix + '_%02d' % i,
    )
    feature_config[str(i)] = tf.tpu.experimental.embedding.FeatureConfig(
        name=str(i),
        table=table_config,
        output_shape=[batch_size] if batch_size else None,
    )
    if max_ids_per_table:
      max_ids_per_table_dict[str(table_name_prefix + '_%02d' % i)] = (
          max_ids_per_table[i]
      )
    if max_unique_ids_per_table:
      max_unique_ids_per_table_dict[str(table_name_prefix + '_%02d' % i)] = (
          max_unique_ids_per_table[i]
      )

  if all((max_ids_per_chip_per_sample, max_ids_per_table,
          max_unique_ids_per_table)):
    sparsecore_config = tf.tpu.experimental.embedding.SparseCoreEmbeddingConfig(
        disable_table_stacking=False,
        max_ids_per_chip_per_sample=max_ids_per_chip_per_sample,
        max_ids_per_table=max_ids_per_table_dict,
        max_unique_ids_per_table=max_unique_ids_per_table_dict,
        allow_id_dropping=allow_id_dropping,
        initialize_tables_on_host=initialize_tables_on_host,
    )

  return feature_config, sparsecore_config