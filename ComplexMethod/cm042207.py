def test_process(cfg, lr, segment, ref_log_msgs, new_log_path, ignore_fields=None, ignore_msgs=None):
  if ignore_fields is None:
    ignore_fields = []
  if ignore_msgs is None:
    ignore_msgs = []

  try:
    log_msgs = replay_process(cfg, lr, disable_progress=True)
  except Exception as e:
    raise Exception("failed on segment: " + segment) from e

  if not check_most_messages_valid(log_msgs):
    return f"Route did not have enough valid messages: {new_log_path}", log_msgs

  # skip this check if the segment is using qcom gps
  if cfg.proc_name != 'ubloxd' or any(m.which() in cfg.pubs for m in lr):
    seen_msgs = {m.which() for m in log_msgs}
    expected_msgs = set(cfg.subs)
    if seen_msgs != expected_msgs:
      return f"Expected messages: {expected_msgs}, but got: {seen_msgs}", log_msgs

  try:
    return compare_logs(ref_log_msgs, log_msgs, ignore_fields + cfg.ignore, ignore_msgs, cfg.tolerance), log_msgs
  except Exception as e:
    return str(e), log_msgs