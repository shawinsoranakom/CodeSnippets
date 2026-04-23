def read_sensor_events(duration_sec):
  socks = {}
  poller = messaging.Poller()
  events = defaultdict(list)
  for config in SENSOR_CONFIGS:
    socks[config.service] = messaging.sub_sock(config.service, poller=poller, timeout=100)

  # wait for sensors to come up
  with Timeout(int(os.environ.get("SENSOR_WAIT", "5")), "sensors didn't come up"):
    while len(poller.poll(250)) == 0:
      pass
  time.sleep(1)
  for s in socks.values():
    messaging.drain_sock_raw(s)

  st = time.monotonic()
  while time.monotonic() - st < duration_sec:
    for s in socks:
      events[s] += messaging.drain_sock(socks[s])
    time.sleep(0.1)
  assert sum(map(len, events.values())) != 0, "No sensor events collected!"

  return {k: v for k, v in events.items() if len(v) > 0}