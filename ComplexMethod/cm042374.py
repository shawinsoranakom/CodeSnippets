def _publish_random_messages(self, services: list[str]) -> dict[str, list]:
    pm = messaging.PubMaster(services)

    managed_processes["loggerd"].start()
    for s in services:
      assert pm.wait_for_readers_to_update(s, timeout=5)

    sent_msgs = defaultdict(list)
    for _ in range(random.randint(2, 10) * 100):
      for s in services:
        try:
          m = messaging.new_message(s)
        except Exception:
          m = messaging.new_message(s, random.randint(2, 10))
        pm.send(s, m)
        sent_msgs[s].append(m)

    for s in services:
      assert pm.wait_for_readers_to_update(s, timeout=5)
    managed_processes["loggerd"].stop()

    return sent_msgs