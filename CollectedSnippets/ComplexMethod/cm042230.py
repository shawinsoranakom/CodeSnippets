def check_most_messages_valid(msgs: LogIterable, threshold: float = 0.9) -> bool:
  relevant_services = {sock for cfg in CONFIGS for sock in cfg.subs}
  msgs_counts = Counter(msg.which() for msg in msgs)
  msgs_valid_counts = Counter(msg.which() for msg in msgs if msg.valid)

  most_valid_for_service = {}
  for msg_type in msgs_counts.keys():
    if msg_type not in relevant_services:
      continue

    valid_share = msgs_valid_counts.get(msg_type, 0) / msgs_counts[msg_type]
    ok = valid_share >= threshold
    if not ok:
      print(f"WARNING: Service {msg_type} has {valid_share * 100:.2f}% valid messages, which is below threshold of {threshold * 100:.2f}%")
    most_valid_for_service[msg_type] = ok

  return all(most_valid_for_service.values())