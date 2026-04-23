def rt_documents(dataset='train',
                 include_unlabeled=True,
                 include_validation=False):
  # pylint:disable=line-too-long
  """Generates Documents for the Rotten Tomatoes dataset.

  Dataset available at http://www.cs.cornell.edu/people/pabo/movie-review-data/
  In this dataset, amazon reviews are used for the unlabeled data.

  Args:
    dataset: str, identifies the data subdirectory.
    include_unlabeled: bool, whether to include the unlabeled data. Only valid
      when dataset=train.
    include_validation: bool, whether to include validation data, which is a
      randomly selected 10% of the data.

  Yields:
    Document

  Raises:
    ValueError: if FLAGS.rt_input_dir is empty.
  """
  # pylint:enable=line-too-long

  if not FLAGS.rt_input_dir:
    raise ValueError('Must provide FLAGS.rt_input_dir')

  tf.logging.info('Generating rt documents...')

  data_files = []
  input_filenames = os.listdir(FLAGS.rt_input_dir)
  for inp_fname in input_filenames:
    if inp_fname.endswith('.pos'):
      data_files.append((os.path.join(FLAGS.rt_input_dir, inp_fname), True))
    elif inp_fname.endswith('.neg'):
      data_files.append((os.path.join(FLAGS.rt_input_dir, inp_fname), False))
  if include_unlabeled and FLAGS.amazon_unlabeled_input_file:
    data_files.append((FLAGS.amazon_unlabeled_input_file, None))

  for filename, class_label in data_files:
    with open(filename) as rt_f:
      for content in rt_f:
        if class_label is None:
          # Process Amazon Review data for unlabeled dataset
          if content.startswith('review/text'):
            yield Document(
                content=content,
                is_validation=False,
                is_test=False,
                label=None,
                add_tokens=False)
        else:
          # 10% of the data is randomly held out for the validation set and
          # another 10% of it is randomly held out for the test set
          random_int = random.randint(1, 10)
          is_validation = random_int == 1
          is_test = random_int == 2
          if (is_test and dataset != 'test') or (is_validation and
                                                 not include_validation):
            continue

          yield Document(
              content=content,
              is_validation=is_validation,
              is_test=is_test,
              label=class_label,
              add_tokens=True)