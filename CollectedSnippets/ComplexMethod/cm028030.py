def __init__(self, hparams):
    self.hparams = hparams
    self.epochs = 0
    self.curr_train_index = 0

    all_labels = []

    self.good_policies = found_policies.good_policies()

    # Determine how many databatched to load
    num_data_batches_to_load = 5
    total_batches_to_load = num_data_batches_to_load
    train_batches_to_load = total_batches_to_load
    assert hparams.train_size + hparams.validation_size <= 50000
    if hparams.eval_test:
      total_batches_to_load += 1
    # Determine how many images we have loaded
    total_dataset_size = 10000 * num_data_batches_to_load
    train_dataset_size = total_dataset_size
    if hparams.eval_test:
      total_dataset_size += 10000

    if hparams.dataset == 'cifar10':
      all_data = np.empty((total_batches_to_load, 10000, 3072), dtype=np.uint8)
    elif hparams.dataset == 'cifar100':
      assert num_data_batches_to_load == 5
      all_data = np.empty((1, 50000, 3072), dtype=np.uint8)
      if hparams.eval_test:
        test_data = np.empty((1, 10000, 3072), dtype=np.uint8)
    if hparams.dataset == 'cifar10':
      tf.logging.info('Cifar10')
      datafiles = [
          'data_batch_1', 'data_batch_2', 'data_batch_3', 'data_batch_4',
          'data_batch_5']

      datafiles = datafiles[:train_batches_to_load]
      if hparams.eval_test:
        datafiles.append('test_batch')
      num_classes = 10
    elif hparams.dataset == 'cifar100':
      datafiles = ['train']
      if hparams.eval_test:
        datafiles.append('test')
      num_classes = 100
    else:
      raise NotImplementedError('Unimplemented dataset: ', hparams.dataset)
    if hparams.dataset != 'test':
      for file_num, f in enumerate(datafiles):
        d = unpickle(os.path.join(hparams.data_path, f))
        if f == 'test':
          test_data[0] = copy.deepcopy(d['data'])
          all_data = np.concatenate([all_data, test_data], axis=1)
        else:
          all_data[file_num] = copy.deepcopy(d['data'])
        if hparams.dataset == 'cifar10':
          labels = np.array(d['labels'])
        else:
          labels = np.array(d['fine_labels'])
        nsamples = len(labels)
        for idx in range(nsamples):
          all_labels.append(labels[idx])

    all_data = all_data.reshape(total_dataset_size, 3072)
    all_data = all_data.reshape(-1, 3, 32, 32)
    all_data = all_data.transpose(0, 2, 3, 1).copy()
    all_data = all_data / 255.0
    mean = augmentation_transforms.MEANS
    std = augmentation_transforms.STDS
    tf.logging.info('mean:{}    std: {}'.format(mean, std))

    all_data = (all_data - mean) / std
    all_labels = np.eye(num_classes)[np.array(all_labels, dtype=np.int32)]
    assert len(all_data) == len(all_labels)
    tf.logging.info(
        'In CIFAR10 loader, number of images: {}'.format(len(all_data)))

    # Break off test data
    if hparams.eval_test:
      self.test_images = all_data[train_dataset_size:]
      self.test_labels = all_labels[train_dataset_size:]

    # Shuffle the rest of the data
    all_data = all_data[:train_dataset_size]
    all_labels = all_labels[:train_dataset_size]
    np.random.seed(0)
    perm = np.arange(len(all_data))
    np.random.shuffle(perm)
    all_data = all_data[perm]
    all_labels = all_labels[perm]

    # Break into train and val
    train_size, val_size = hparams.train_size, hparams.validation_size
    assert 50000 >= train_size + val_size
    self.train_images = all_data[:train_size]
    self.train_labels = all_labels[:train_size]
    self.val_images = all_data[train_size:train_size + val_size]
    self.val_labels = all_labels[train_size:train_size + val_size]
    self.num_train = self.train_images.shape[0]