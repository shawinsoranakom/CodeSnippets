def rcv1_documents(dataset='train',
                   include_unlabeled=True,
                   include_validation=False):
  # pylint:disable=line-too-long
  """Generates Documents for Reuters Corpus (rcv1) dataset.

  Dataset described at
  http://www.ai.mit.edu/projects/jmlr/papers/volume5/lewis04a/lyrl2004_rcv1v2_README.htm

  Args:
    dataset: str, identifies the csv file within the rcv1 data directory.
    include_unlabeled: bool, whether to include the unlab file. Only valid
      when dataset=train.
    include_validation: bool, whether to include validation data, which is a
      randomly selected 10% of the data.

  Yields:
    Document

  Raises:
    ValueError: if FLAGS.rcv1_input_dir is empty.
  """
  # pylint:enable=line-too-long

  if not FLAGS.rcv1_input_dir:
    raise ValueError('Must provide FLAGS.rcv1_input_dir')

  tf.logging.info('Generating rcv1 documents...')

  datasets = [dataset]
  if include_unlabeled:
    if dataset == 'train':
      datasets.append('unlab')
  for dset in datasets:
    with open(os.path.join(FLAGS.rcv1_input_dir, dset + '.csv')) as db_f:
      reader = csv.reader(db_f)
      for row in reader:
        # 10% of the data is randomly held out
        is_validation = random.randint(1, 10) == 1
        if is_validation and not include_validation:
          continue

        content = row[1]
        yield Document(
            content=content,
            is_validation=is_validation,
            is_test=False,
            label=int(row[0]),
            add_tokens=True)