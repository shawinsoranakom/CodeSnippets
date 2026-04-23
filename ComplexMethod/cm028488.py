def get_input_fn(
    tfrecord_dir,
    split,
    bsz_per_host,
    seq_len,
    reuse_len,
    bi_data,
    num_hosts=1,
    num_core_per_host=1,
    perm_size=None,
    mask_alpha=None,
    mask_beta=None,
    uncased=False,
    num_passes=None,
    use_bfloat16=False,
    num_predict=None):
  """Gets the input function."""

  # Merge all record infos into a single one
  record_glob_base = format_filename(
      prefix="record_info-{}-*".format(split),
      bsz_per_host=bsz_per_host,
      seq_len=seq_len,
      bi_data=bi_data,
      suffix="json",
      mask_alpha=mask_alpha,
      mask_beta=mask_beta,
      reuse_len=reuse_len,
      uncased=uncased,
      fixed_num_predict=num_predict)

  record_info = {"num_batch": 0, "filenames": []}

  tfrecord_dirs = tfrecord_dir.split(",")
  logging.info("Use the following tfrecord dirs: %s", tfrecord_dirs)

  for idx, record_dir in enumerate(tfrecord_dirs):
    record_glob = os.path.join(record_dir, record_glob_base)
    logging.info("[%d] Record glob: %s", idx, record_glob)

    record_paths = sorted(tf.gfile.Glob(record_glob))
    logging.info("[%d] Num of record info path: %d", idx, len(record_paths))

    cur_record_info = {"num_batch": 0, "filenames": []}

    for record_info_path in record_paths:
      if num_passes is not None:
        record_info_name = os.path.basename(record_info_path)
        fields = record_info_name.split(".")[0].split("-")
        pass_id = int(fields[-1])
        if len(fields) == 5 and pass_id >= num_passes:
          logging.info("Skip pass %d: %s", pass_id, record_info_name)
          continue

      with tf.gfile.Open(record_info_path, "r") as fp:
        info = json.load(fp)
        if num_passes is not None:
          eff_num_passes = min(num_passes, len(info["filenames"]))
          ratio = eff_num_passes / len(info["filenames"])
          cur_record_info["num_batch"] += int(info["num_batch"] * ratio)
          cur_record_info["filenames"] += info["filenames"][:eff_num_passes]
        else:
          cur_record_info["num_batch"] += info["num_batch"]
          cur_record_info["filenames"] += info["filenames"]

    # overwrite directory for `cur_record_info`
    new_filenames = []
    for filename in cur_record_info["filenames"]:
      basename = os.path.basename(filename)
      new_filename = os.path.join(record_dir, basename)
      new_filenames.append(new_filename)
    cur_record_info["filenames"] = new_filenames

    logging.info("[Dir %d] Number of chosen batches: %s",
                 idx, cur_record_info["num_batch"])
    logging.info("[Dir %d] Number of chosen files: %s",
                 idx, len(cur_record_info["filenames"]))
    logging.info(cur_record_info["filenames"])

    # add `cur_record_info` to global `record_info`
    record_info["num_batch"] += cur_record_info["num_batch"]
    record_info["filenames"] += cur_record_info["filenames"]

  logging.info("Total number of batches: %d", record_info["num_batch"])
  logging.info("Total number of files: %d", len(record_info["filenames"]))
  logging.info(record_info["filenames"])

  def input_fn(params):
    """docs."""
    assert params["batch_size"] * num_core_per_host == bsz_per_host

    dataset = get_dataset(
        params=params,
        num_hosts=num_hosts,
        num_core_per_host=num_core_per_host,
        split=split,
        file_names=record_info["filenames"],
        num_batch=record_info["num_batch"],
        seq_len=seq_len,
        reuse_len=reuse_len,
        perm_size=perm_size,
        mask_alpha=mask_alpha,
        mask_beta=mask_beta,
        use_bfloat16=use_bfloat16,
        num_predict=num_predict)

    return dataset

  return input_fn, record_info