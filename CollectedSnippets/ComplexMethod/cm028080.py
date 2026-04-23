def train_val_one_epoch(
        loader, model, criterion, optimizer, epoch, train=True, batch_size=5,
        query_size=2000, neg_num=5, update_every=1, debug=False):
  """Executes either training or validation step based on `train` value.

  Args:
    loader: Training/validation iterable dataset.
    model: Network to train/validate.
    criterion: Loss function.
    optimizer: Network optimizer.
    epoch: Integer, epoch number.
    train: Bool, specifies training or validation phase.
    batch_size: Integer, number of (q,p,n1,...,nN) tuples in a mini-batch.
    query_size: Integer, number of queries randomly drawn per one training
      epoch.
    neg_num: Integer, number of negatives per a tuple.
    update_every: Integer, update model weights every N batches, used to
      handle relatively large batches batch_size effectively becomes
      update_every x batch_size.
    debug: Bool, whether debug mode is used.

  Returns:
    average_epoch_loss: Average epoch loss.
  """
  batch_time = global_features_utils.AverageMeter()
  data_time = global_features_utils.AverageMeter()
  losses = global_features_utils.AverageMeter()

  # Retrieve all trainable variables we defined in the graph.
  tvs = model.trainable_variables
  accum_grads = [tf.zeros_like(tv.read_value()) for tv in tvs]

  end = time.time()
  batch_num = 0
  print_frequency = 10
  all_batch_num = query_size // batch_size
  state = 'Train' if train else 'Val'
  global_features_utils.debug_and_log('>> {} step:'.format(state))

  # For every batch in the dataset; Stops when all batches in the dataset have
  # been processed.
  while True:
    data_time.update(time.time() - end)

    if train:
      try:
        # Train on one batch.
        # Each image in the batch is loaded into memory consecutively.
        for _ in range(batch_size):
          # Because the images are not necessarily of the same size, we can't
          # set the batch size with .batch().
          batch = loader.get_next()
          input_tuple = batch[0:-1]
          target_tuple = batch[-1]

          loss_value, grads = _compute_loss_and_gradient(
                  criterion, model, input_tuple, target_tuple, neg_num)
          losses.update(loss_value)
          # Accumulate gradients.
          accum_grads += grads

        # Perform weight update if required.
        if (batch_num + 1) % update_every == 0 or (
                batch_num + 1) == all_batch_num:
          # Do one step for multiple batches. Accumulated gradients are
          # used.
          optimizer.apply_gradients(
                  zip(accum_grads, model.trainable_variables))
          accum_grads = [tf.zeros_like(tv.read_value()) for tv in tvs]
      # We break when we run out of range, i.e., we exhausted all dataset
      # images.
      except tf.errors.OutOfRangeError:
        break

    else:
      # Validate one batch.
      # We load full batch into memory.
      input = []
      target = []
      try:
        for _ in range(batch_size):
          # Because the images are not necessarily of the same size, we can't
          # set the batch size with .batch().
          batch = loader.get_next()
          input.append(batch[0:-1])
          target.append(batch[-1])
      # We break when we run out of range, i.e., we exhausted all dataset
      # images.
      except tf.errors.OutOfRangeError:
        break

      descriptors = tf.zeros(shape=(0, model.meta['outputdim']),
                             dtype=tf.float32)

      for input_tuple in input:
        for img in input_tuple:
          # Compute the global descriptor vector.
          model_out = model(tf.expand_dims(img, axis=0), training=False)
          descriptors = tf.concat([descriptors, model_out], 0)

      # No need to reduce memory consumption (no backward pass):
      # Compute loss for the full batch.
      queries = descriptors[target == -1]
      positives = descriptors[target == 1]
      negatives = descriptors[target == 0]
      negatives = tf.reshape(negatives, [tf.shape(queries)[0], neg_num,
                                         model.meta['outputdim']])
      loss = criterion(queries, positives, negatives)

      # Record loss.
      losses.update(loss / batch_size, batch_size)

    # Measure elapsed time.
    batch_time.update(time.time() - end)
    end = time.time()

    # Record immediate loss and elapsed time.
    if debug and ((batch_num + 1) % print_frequency == 0 or
                  batch_num == 0 or (batch_num + 1) == all_batch_num):
      global_features_utils.debug_and_log(
              '>> {0}: [{1} epoch][{2}/{3} batch]\t Time val: {'
              'batch_time.val:.3f} '
              '(Batch Time avg: {batch_time.avg:.3f})\t Data {'
              'data_time.val:.3f} ('
              'Time avg: {data_time.avg:.3f})\t Immediate loss value: {'
              'loss.val:.4f} '
              '(Loss avg: {loss.avg:.4f})'.format(
                      state, epoch, batch_num + 1, all_batch_num,
                      batch_time=batch_time,
                      data_time=data_time, loss=losses), debug=True, log=False)
    batch_num += 1

  return losses.avg