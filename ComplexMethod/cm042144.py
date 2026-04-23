def __init__(self, services: List[str], poll: Optional[str] = None,
               ignore_alive: Optional[List[str]] = None, ignore_avg_freq: Optional[List[str]] = None,
               ignore_valid: Optional[List[str]] = None, addr: str = "127.0.0.1", frequency: Optional[float] = None):
    self.frame = -1
    self.services = services
    self.seen = {s: False for s in services}
    self.updated = {s: False for s in services}
    self.recv_time = {s: 0. for s in services}
    self.recv_frame = {s: 0 for s in services}
    self.sock = {}
    self.data = {}
    self.logMonoTime = {s: 0 for s in services}

    # zero-frequency / on-demand services are always alive and presumed valid; all others must pass checks
    on_demand = {s: SERVICE_LIST[s].frequency <= 1e-5 for s in services}
    self.static_freq_services = set(s for s in services if not on_demand[s])
    self.alive = {s: on_demand[s] for s in services}
    self.freq_ok = {s: on_demand[s] for s in services}
    self.valid = {s: on_demand[s] for s in services}

    self.freq_tracker: Dict[str, FrequencyTracker] = {}
    self.poller = Poller()
    polled_services = set([poll, ] if poll is not None else services)
    self.non_polled_services = set(services) - polled_services

    self.ignore_average_freq = [] if ignore_avg_freq is None else ignore_avg_freq
    self.ignore_alive = [] if ignore_alive is None else ignore_alive
    self.ignore_valid = [] if ignore_valid is None else ignore_valid

    self.simulation = bool(int(os.getenv("SIMULATION", "0")))

    # if freq and poll aren't specified, assume the max to be conservative
    assert frequency is None or poll is None, "Do not specify 'frequency' - frequency of the polled service will be used."
    self.update_freq = frequency or max([SERVICE_LIST[s].frequency for s in polled_services])

    for s in services:
      p = self.poller if s not in self.non_polled_services else None
      self.sock[s] = sub_sock(s, poller=p, addr=addr, conflate=True)

      try:
        data = new_message(s)
      except capnp.lib.capnp.KjException:
        data = new_message(s, 0) # lists

      self.data[s] = getattr(data.as_reader(), s)
      self.freq_tracker[s] = FrequencyTracker(SERVICE_LIST[s].frequency, self.update_freq, s == poll)