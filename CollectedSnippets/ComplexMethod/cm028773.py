def get_tfrecord_name(
    per_host_batch_size: int,
    num_cores_per_host: int,
    seq_length: int,
    bi_data: bool,
    reuse_length: int,
    do_lower_case: bool,
    use_eod_token: bool,
    prefix: str = "",
    suffix: str = "",
    pass_id: int = 0,
    num_passes: int = 1,
    task_id: int = None,
    num_tasks: int = None) -> str:
  """Formats the resulting TFRecord name based on provided inputs."""
  components = []
  if prefix:
    components.append(prefix)
  components.append("seqlen-{}".format(seq_length))
  if reuse_length == 0:
    components.append("memless")
  else:
    components.append("reuse-{}".format(reuse_length))
  components.append("bs-{}".format(per_host_batch_size))
  components.append("cores-{}".format(num_cores_per_host))

  if do_lower_case:
    components.append("uncased")
  else:
    components.append("cased")
  if use_eod_token:
    components.append("eod")
  if bi_data:
    components.append("bi")
  else:
    components.append("uni")

  if suffix:
    components.append(suffix)

  s = "_".join(components) + ".tfrecord"
  if num_passes == 1 and task_id is None:
    return s

  if task_id is None:
    num_tasks = 1
    task_id = 0

  current_shard = task_id * num_passes + pass_id
  total_shards = num_tasks * num_passes
  return s + "-{}-of-{}".format(current_shard, total_shards)