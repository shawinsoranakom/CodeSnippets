def create_data(_):
  """Creates pretrain data."""
  # Validate FLAGS
  assert FLAGS.bsz_per_host % FLAGS.num_core_per_host == 0
  if not FLAGS.use_tpu:
    FLAGS.num_core_per_host = 1  # forced to be one

  # Make workdirs
  if not tf.gfile.Exists(FLAGS.save_dir):
    tf.gfile.MakeDirs(FLAGS.save_dir)

  tfrecord_dir = os.path.join(FLAGS.save_dir, "tfrecords")
  if not tf.gfile.Exists(tfrecord_dir):
    tf.gfile.MakeDirs(tfrecord_dir)

  # Create and dump corpus_info from task 0
  if FLAGS.task == 0 and FLAGS.pass_id == 0:
    corpus_info = {
        "vocab_size": VOCAB_SIZE,
        "bsz_per_host": FLAGS.bsz_per_host,
        "num_core_per_host": FLAGS.num_core_per_host,
        "seq_len": FLAGS.seq_len,
        "reuse_len": FLAGS.reuse_len,
        "uncased": FLAGS.uncased,
        "bi_data": FLAGS.bi_data,
        "mask_alpha": FLAGS.mask_alpha,
        "mask_beta": FLAGS.mask_beta,
        "num_predict": FLAGS.num_predict,
        "use_eod": FLAGS.use_eod,
        "sp_path": FLAGS.sp_path,
        "input_glob": FLAGS.input_glob,
    }
    corpus_info_path = os.path.join(FLAGS.save_dir, "corpus_info.json")
    with tf.gfile.Open(corpus_info_path, "w") as fp:
      json.dump(corpus_info, fp)

  # Interleavely split the work into FLAGS.num_task splits
  file_paths = sorted(tf.gfile.Glob(FLAGS.input_glob))
  logging.info("Use glob: %s", FLAGS.input_glob)
  logging.info("Find %d files: %s", len(file_paths), file_paths)

  task_file_paths = file_paths[FLAGS.task::FLAGS.num_task]
  if not task_file_paths:
    logging.info("Exit: task %d has no file to process.", FLAGS.task)
    return

  logging.info("Task %d process %d files: %s",
               FLAGS.task, len(task_file_paths), task_file_paths)
  record_info = _create_data(FLAGS.task, task_file_paths)

  record_prefix = "record_info-{}-{}-{}".format(
      FLAGS.split, FLAGS.task, FLAGS.pass_id)
  record_name = format_filename(
      prefix=record_prefix,
      bsz_per_host=FLAGS.bsz_per_host,
      seq_len=FLAGS.seq_len,
      mask_alpha=FLAGS.mask_alpha,
      mask_beta=FLAGS.mask_beta,
      reuse_len=FLAGS.reuse_len,
      bi_data=FLAGS.bi_data,
      suffix="json",
      uncased=FLAGS.uncased,
      fixed_num_predict=FLAGS.num_predict)
  record_info_path = os.path.join(tfrecord_dir, record_name)

  with tf.gfile.Open(record_info_path, "w") as fp:
    json.dump(record_info, fp)