def encode_and_save_files(subtokenizer, data_dir, raw_files, tag, total_shards):
  """Save data from files as encoded Examples in TFrecord format.

  Args:
    subtokenizer: Subtokenizer object that will be used to encode the strings.
    data_dir: The directory in which to write the examples
    raw_files: A tuple of (input, target) data files. Each line in the input and
      the corresponding line in target file will be saved in a tf.Example.
    tag: String that will be added onto the file names.
    total_shards: Number of files to divide the data into.

  Returns:
    List of all files produced.
  """
  # Create a file for each shard.
  filepaths = [
      shard_filename(data_dir, tag, n + 1, total_shards)
      for n in range(total_shards)
  ]

  if all_exist(filepaths):
    logging.info("Files with tag %s already exist.", tag)
    return filepaths

  logging.info("Saving files with tag %s.", tag)
  input_file = raw_files[0]
  target_file = raw_files[1]

  # Write examples to each shard in round robin order.
  tmp_filepaths = [six.ensure_str(fname) + ".incomplete" for fname in filepaths]
  writers = [tf.python_io.TFRecordWriter(fname) for fname in tmp_filepaths]
  counter, shard = 0, 0
  for counter, (input_line, target_line) in enumerate(
      zip(txt_line_iterator(input_file), txt_line_iterator(target_file))):
    if counter > 0 and counter % 100000 == 0:
      logging.info("\tSaving case %d.", counter)
    example = dict_to_example({
        "inputs": subtokenizer.encode(input_line, add_eos=True),
        "targets": subtokenizer.encode(target_line, add_eos=True)
    })
    writers[shard].write(example.SerializeToString())
    shard = (shard + 1) % total_shards
  for writer in writers:
    writer.close()

  for tmp_name, final_name in zip(tmp_filepaths, filepaths):
    tf.gfile.Rename(tmp_name, final_name)

  logging.info("Saved %d Examples", counter + 1)
  return filepaths