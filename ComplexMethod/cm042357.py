def get_power_with_warmup_for_target(self, proc, prev):
    socks = {msg: messaging.sub_sock(msg) for msg in proc.msgs}
    for sock in socks.values():
      messaging.drain_sock_raw(sock)

    msgs_and_power = deque([], maxlen=SAMPLE_TIME)

    start_time = time.monotonic()

    while (time.monotonic() - start_time) < MAX_WARMUP_TIME:
      power = get_power(1)
      iteration_msg_counts = {}
      for msg,sock in socks.items():
        iteration_msg_counts[msg] = len(messaging.drain_sock_raw(sock))
      msgs_and_power.append((power, iteration_msg_counts))

      if len(msgs_and_power) < SAMPLE_TIME:
        continue

      msg_counts = self.tabulate_msg_counts(msgs_and_power)
      now = np.mean([m[0] for m in msgs_and_power])

      if self.valid_msg_count(proc, msg_counts) and self.valid_power_draw(proc, now - prev):
        break

    return now, msg_counts, time.monotonic() - start_time - SAMPLE_TIME