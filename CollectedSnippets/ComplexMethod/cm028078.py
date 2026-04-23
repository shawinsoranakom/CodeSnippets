def _build_train_and_validation_splits(image_paths, file_ids, labels,
                                       validation_split_size, seed):
  """Create TRAIN and VALIDATION splits containing all labels in equal proportion.

  Args:
    image_paths: list of paths to the image files in the train dataset.
    file_ids: list of image file ids in the train dataset.
    labels: list of image labels in the train dataset.
    validation_split_size: size of the VALIDATION split as a ratio of the train
      dataset.
    seed: seed to use for shuffling the dataset for reproducibility purposes.

  Returns:
    splits : tuple containing the TRAIN and VALIDATION splits.
  Raises:
    ValueError: if the image attributes arrays don't all have the same length,
                which makes the shuffling impossible.
  """
  # Ensure all image attribute arrays have the same length.
  total_images = len(file_ids)
  if not (len(image_paths) == total_images and len(labels) == total_images):
    raise ValueError('Inconsistencies between number of file_ids (%d), number '
                     'of image_paths (%d) and number of labels (%d). Cannot'
                     'shuffle the train dataset.'% (total_images,
                                                    len(image_paths),
                                                    len(labels)))

  # Stack all image attributes arrays in a single 2D array of dimensions
  # (3, number of images) and group by label the indices of datapoins in the
  # image attributes arrays. Explicitly convert label types from 'int' to 'str'
  # to avoid implicit conversion during stacking with image_paths and file_ids
  # which are 'str'.
  labels_str = [str(label) for label in labels]
  image_attrs = np.stack((image_paths, file_ids, labels_str))
  image_attrs_idx_by_label = {}
  for index, label in enumerate(labels):
    if label not in image_attrs_idx_by_label:
      image_attrs_idx_by_label[label] = []
    image_attrs_idx_by_label[label].append(index)

  # Create subsets of image attributes by label, shuffle them separately and
  # split each subset into TRAIN and VALIDATION splits based on the size of the
  # validation split.
  splits = {
      _VALIDATION_SPLIT: [],
      _TRAIN_SPLIT: []
  }
  rs = np.random.RandomState(np.random.MT19937(np.random.SeedSequence(seed)))
  for label, indexes in image_attrs_idx_by_label.items():
    # Create the subset for the current label.
    image_attrs_label = image_attrs[:, indexes]
    # Shuffle the current label subset.
    image_attrs_label = _shuffle_by_columns(image_attrs_label, rs)
    # Split the current label subset into TRAIN and VALIDATION splits and add
    # each split to the list of all splits.
    images_per_label = image_attrs_label.shape[1]
    cutoff_idx = max(1, int(validation_split_size * images_per_label))
    splits[_VALIDATION_SPLIT].append(image_attrs_label[:, 0 : cutoff_idx])
    splits[_TRAIN_SPLIT].append(image_attrs_label[:, cutoff_idx : ])

  # Concatenate all subsets of image attributes into TRAIN and VALIDATION splits
  # and reshuffle them again to ensure variance of labels across batches.
  validation_split = _shuffle_by_columns(
      np.concatenate(splits[_VALIDATION_SPLIT], axis=1), rs)
  train_split = _shuffle_by_columns(
      np.concatenate(splits[_TRAIN_SPLIT], axis=1), rs)

  # Unstack the image attribute arrays in the TRAIN and VALIDATION splits and
  # convert them back to lists. Convert labels back to 'int' from 'str'
  # following the explicit type change from 'str' to 'int' for stacking.
  return (
      {
          _IMAGE_PATHS_KEY: validation_split[0, :].tolist(),
          _FILE_IDS_KEY: validation_split[1, :].tolist(),
          _LABELS_KEY: [int(label) for label in validation_split[2, :].tolist()]
      }, {
          _IMAGE_PATHS_KEY: train_split[0, :].tolist(),
          _FILE_IDS_KEY: train_split[1, :].tolist(),
          _LABELS_KEY: [int(label) for label in train_split[2, :].tolist()]
      })