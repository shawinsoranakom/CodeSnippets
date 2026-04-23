def trim_logs(logs, start_frame, end_frame, frs_types, include_all_types):
  all_msgs = []
  cam_state_counts = defaultdict(int)
  for msg in sorted(logs, key=lambda m: m.logMonoTime):
    if msg.which() in frs_types:
      cam_state_counts[msg.which()] += 1
    if any(cam_state_counts[state]  >= start_frame for state in frs_types):
      all_msgs.append(msg)
    if all(cam_state_counts[state] == end_frame for state in frs_types):
      break

  if len(include_all_types) != 0:
    other_msgs = [m for m in logs if m.which() in include_all_types]
    all_msgs.extend(other_msgs)

  return all_msgs