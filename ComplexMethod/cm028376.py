def _generate_data():
  """Extract sequences from dataset_dir and store them in data_dir."""
  if not gfile.Exists(FLAGS.data_dir):
    gfile.MakeDirs(FLAGS.data_dir)

  global dataloader  # pylint: disable=global-variable-undefined
  if FLAGS.dataset_name == 'bike':
    dataloader = dataset_loader.Bike(FLAGS.dataset_dir,
                                     img_height=FLAGS.img_height,
                                     img_width=FLAGS.img_width,
                                     seq_length=FLAGS.seq_length)
  elif FLAGS.dataset_name == 'kitti_odom':
    dataloader = dataset_loader.KittiOdom(FLAGS.dataset_dir,
                                          img_height=FLAGS.img_height,
                                          img_width=FLAGS.img_width,
                                          seq_length=FLAGS.seq_length)
  elif FLAGS.dataset_name == 'kitti_raw_eigen':
    dataloader = dataset_loader.KittiRaw(FLAGS.dataset_dir,
                                         split='eigen',
                                         img_height=FLAGS.img_height,
                                         img_width=FLAGS.img_width,
                                         seq_length=FLAGS.seq_length)
  elif FLAGS.dataset_name == 'kitti_raw_stereo':
    dataloader = dataset_loader.KittiRaw(FLAGS.dataset_dir,
                                         split='stereo',
                                         img_height=FLAGS.img_height,
                                         img_width=FLAGS.img_width,
                                         seq_length=FLAGS.seq_length)
  elif FLAGS.dataset_name == 'cityscapes':
    dataloader = dataset_loader.Cityscapes(FLAGS.dataset_dir,
                                           img_height=FLAGS.img_height,
                                           img_width=FLAGS.img_width,
                                           seq_length=FLAGS.seq_length)
  else:
    raise ValueError('Unknown dataset')

  # The default loop below uses multiprocessing, which can make it difficult
  # to locate source of errors in data loader classes.
  # Uncomment this loop for easier debugging:

  # all_examples = {}
  # for i in range(dataloader.num_train):
  #   _gen_example(i, all_examples)
  #   logging.info('Generated: %d', len(all_examples))

  all_frames = range(dataloader.num_train)
  frame_chunks = np.array_split(all_frames, NUM_CHUNKS)

  manager = multiprocessing.Manager()
  all_examples = manager.dict()
  num_cores = multiprocessing.cpu_count()
  num_threads = num_cores if FLAGS.num_threads is None else FLAGS.num_threads
  pool = multiprocessing.Pool(num_threads)

  # Split into training/validation sets. Fixed seed for repeatability.
  np.random.seed(8964)

  if not gfile.Exists(FLAGS.data_dir):
    gfile.MakeDirs(FLAGS.data_dir)

  with gfile.Open(os.path.join(FLAGS.data_dir, 'train.txt'), 'w') as train_f:
    with gfile.Open(os.path.join(FLAGS.data_dir, 'val.txt'), 'w') as val_f:
      logging.info('Generating data...')
      for index, frame_chunk in enumerate(frame_chunks):
        all_examples.clear()
        pool.map(_gen_example_star,
                 itertools.izip(frame_chunk, itertools.repeat(all_examples)))
        logging.info('Chunk %d/%d: saving %s entries...', index + 1, NUM_CHUNKS,
                     len(all_examples))
        for _, example in all_examples.items():
          if example:
            s = example['folder_name']
            frame = example['file_name']
            if np.random.random() < 0.1:
              val_f.write('%s %s\n' % (s, frame))
            else:
              train_f.write('%s %s\n' % (s, frame))
  pool.close()
  pool.join()