def documents(dataset='train',
              include_unlabeled=False,
              include_validation=False):
  """Generates Documents based on FLAGS.dataset.

  Args:
    dataset: str, identifies folder within IMDB data directory, test or train.
    include_unlabeled: bool, whether to include the unsup directory. Only valid
      when dataset=train.
    include_validation: bool, whether to include validation data.

  Yields:
    Document

  Raises:
    ValueError: if include_unlabeled is true but dataset is not 'train'
  """

  if include_unlabeled and dataset != 'train':
    raise ValueError('If include_unlabeled=True, must use train dataset')

  # Set the random seed so that we have the same validation set when running
  # gen_data and gen_vocab.
  random.seed(302)

  ds = FLAGS.dataset
  if ds == 'imdb':
    docs_gen = imdb_documents
  elif ds == 'dbpedia':
    docs_gen = dbpedia_documents
  elif ds == 'rcv1':
    docs_gen = rcv1_documents
  elif ds == 'rt':
    docs_gen = rt_documents
  else:
    raise ValueError('Unrecognized dataset %s' % FLAGS.dataset)

  for doc in docs_gen(dataset, include_unlabeled, include_validation):
    yield doc