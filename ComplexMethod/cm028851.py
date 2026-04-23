def write_tf_record_dataset(output_path, annotation_iterator,
                            process_func, num_shards,
                            multiple_processes=None, unpack_arguments=True):
  """Iterates over annotations, processes them and writes into TFRecords.

  Args:
    output_path: The prefix path to create TF record files.
    annotation_iterator: An iterator of tuples containing details about the
      dataset.
    process_func: A function which takes the elements from the tuples of
      annotation_iterator as arguments and returns a tuple of (tf.train.Example,
      int). The integer indicates the number of annotations that were skipped.
    num_shards: int, the number of shards to write for the dataset.
    multiple_processes: integer, the number of multiple parallel processes to
      use.  If None, uses multi-processing with number of processes equal to
      `os.cpu_count()`, which is Python's default behavior. If set to 0,
      multi-processing is disabled.
      Whether or not to use multiple processes to write TF Records.
    unpack_arguments:
      Whether to unpack the tuples from annotation_iterator as individual
        arguments to the process func or to pass the returned value as it is.

  Returns:
    num_skipped: The total number of skipped annotations.
  """

  writers = [
      tf.io.TFRecordWriter(
          output_path + '-%05d-of-%05d.tfrecord' % (i, num_shards))
      for i in range(num_shards)
  ]

  total_num_annotations_skipped = 0

  if multiple_processes is None or multiple_processes > 0:
    pool = mp.Pool(
        processes=multiple_processes)
    if unpack_arguments:
      tf_example_iterator = pool.starmap(process_func, annotation_iterator)
    else:
      tf_example_iterator = pool.imap(process_func, annotation_iterator)
  else:
    if unpack_arguments:
      tf_example_iterator = itertools.starmap(process_func, annotation_iterator)
    else:
      tf_example_iterator = map(process_func, annotation_iterator)

  for idx, (tf_example, num_annotations_skipped) in enumerate(
      tf_example_iterator):
    if idx % LOG_EVERY == 0:
      logging.info('On image %d', idx)

    total_num_annotations_skipped += num_annotations_skipped
    writers[idx % num_shards].write(tf_example.SerializeToString())

  if multiple_processes is None or multiple_processes > 0:
    pool.close()
    pool.join()

  for writer in writers:
    writer.close()

  logging.info('Finished writing, skipped %d annotations.',
               total_num_annotations_skipped)
  return total_num_annotations_skipped