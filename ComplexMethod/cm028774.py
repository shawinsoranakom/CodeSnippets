def create_tfrecords(
    tokenizer: tokenization.FullSentencePieceTokenizer,
    input_file_or_files: str,
    use_eod_token: bool,
    do_lower_case: bool,
    per_host_batch_size: int,
    seq_length: int,
    reuse_length: int,
    bi_data: bool,
    num_cores_per_host: int,
    save_dir: str,
    prefix: str = "",
    suffix: str = "",
    num_tasks: Optional[int] = None,
    task_id: Optional[int] = None,
    num_passes: int = 1):
  """Runs the end-to-end preprocessing pipeline."""

  logging.info("Input configuration:")
  logging.info("input file(s): %s", input_file_or_files)
  logging.info("use_eod_token: %s", use_eod_token)
  logging.info("do_lower_case: %s", do_lower_case)
  logging.info("per_host_batch_size: %d", per_host_batch_size)
  logging.info("seq_length: %d", seq_length)
  logging.info("reuse_length: %d", reuse_length)
  logging.info("bi_data: %s", bi_data)
  logging.info("num_cores_per_host: %d", num_cores_per_host)
  logging.info("save_dir: %s", save_dir)
  if task_id is not None and num_tasks is not None:
    logging.info("task_id: %d", task_id)
    logging.info("num_tasks: %d", num_tasks)

  input_files = []
  for input_pattern in input_file_or_files.split(","):
    input_files.extend(tf.io.gfile.glob(input_pattern))

  logging.info("*** Reading from input files ***")
  for input_file in input_files:
    logging.info("  %s", input_file)

  logging.info("Shuffling the files with a fixed random seed.")
  np.random.shuffle(input_files)
  if num_tasks is not None:
    assert task_id is not None
    logging.info("Total number of input files: %d", len(input_files))
    logging.info("Splitting into %d shards of %d files each.",
                 num_tasks, len(input_files) // num_tasks)
    input_files = input_files[task_id::num_tasks]

  all_data = preprocess_and_tokenize_input_files(
      input_files=input_files,
      tokenizer=tokenizer,
      use_eod=use_eod_token,
      do_lower_case=do_lower_case)
  for pass_id in range(num_passes):
    logging.info("Beginning pass %d of %d", pass_id, num_passes)
    tokens, sentence_ids = shuffle_and_combine_preprocessed_data(all_data)

    assert len(tokens) == len(sentence_ids)

    filename = get_tfrecord_name(
        per_host_batch_size=per_host_batch_size,
        num_cores_per_host=num_cores_per_host,
        seq_length=seq_length,
        bi_data=bi_data,
        use_eod_token=use_eod_token,
        reuse_length=reuse_length,
        do_lower_case=do_lower_case,
        prefix=prefix,
        suffix=suffix,
        pass_id=pass_id,
        num_passes=num_passes,
        num_tasks=num_tasks,
        task_id=task_id)
    save_path = os.path.join(save_dir, filename)
    if os.path.exists(save_path):
      # If the path already exists, then we were probably preempted but
      # previously wrote this file.
      logging.info("%s already exists, skipping this batch.", save_path)
    else:
      instances = _convert_tokens_to_instances(
          tokenizer=tokenizer,
          tokens=tokens,
          sentence_ids=sentence_ids,
          per_host_batch_size=per_host_batch_size,
          seq_length=seq_length,
          reuse_length=reuse_length,
          bi_data=bi_data,
          num_cores_per_host=num_cores_per_host)
      write_instances_to_tfrecord(instances=instances, save_path=save_path)

  if task_id is None or task_id == 0:
    corpus_info = {
        "vocab_size": 32000,
        "per_host_batch_size": per_host_batch_size,
        "num_cores_per_host": num_cores_per_host,
        "seq_length": seq_length,
        "reuse_length": reuse_length,
        "do_lower_case": do_lower_case,
        "bi_data": bi_data,
        "use_eod_token": use_eod_token,
    }
    corpus_fname = os.path.basename(filename) + ".json"
    corpus_destination = os.path.join(save_dir, corpus_fname)
    logging.info("Saving corpus info to %s", corpus_destination)

    with tf.io.gfile.GFile(corpus_destination, "w") as fp:
      json.dump(corpus_info, fp)