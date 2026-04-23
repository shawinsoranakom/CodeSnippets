def imdb_documents(dataset='train',
                   include_unlabeled=False,
                   include_validation=False):
  """Generates Documents for IMDB dataset.

  Data from http://ai.stanford.edu/~amaas/data/sentiment/

  Args:
    dataset: str, identifies folder within IMDB data directory, test or train.
    include_unlabeled: bool, whether to include the unsup directory. Only valid
      when dataset=train.
    include_validation: bool, whether to include validation data.

  Yields:
    Document

  Raises:
    ValueError: if FLAGS.imdb_input_dir is empty.
  """
  if not FLAGS.imdb_input_dir:
    raise ValueError('Must provide FLAGS.imdb_input_dir')

  tf.logging.info('Generating IMDB documents...')

  def check_is_validation(filename, class_label):
    if class_label is None:
      return False
    file_idx = int(filename.split('_')[0])
    is_pos_valid = (class_label and
                    file_idx >= FLAGS.imdb_validation_pos_start_id)
    is_neg_valid = (not class_label and
                    file_idx >= FLAGS.imdb_validation_neg_start_id)
    return is_pos_valid or is_neg_valid

  dirs = [(dataset + '/pos', True), (dataset + '/neg', False)]
  if include_unlabeled:
    dirs.append(('train/unsup', None))

  for d, class_label in dirs:
    for filename in os.listdir(os.path.join(FLAGS.imdb_input_dir, d)):
      is_validation = check_is_validation(filename, class_label)
      if is_validation and not include_validation:
        continue

      with open(os.path.join(FLAGS.imdb_input_dir, d, filename), encoding='utf-8') as imdb_f:
        content = imdb_f.read()
      yield Document(
          content=content,
          is_validation=is_validation,
          is_test=False,
          label=class_label,
          add_tokens=True)

  if FLAGS.amazon_unlabeled_input_file and include_unlabeled:
    with open(FLAGS.amazon_unlabeled_input_file, encoding='utf-8') as rt_f:
      for content in rt_f:
        yield Document(
            content=content,
            is_validation=False,
            is_test=False,
            label=None,
            add_tokens=False)