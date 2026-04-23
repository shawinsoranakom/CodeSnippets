def main(route: str | None, addrs: list[int], rxoffset: int | None):
  """
  TODO:
  - highlight TX vs RX clearly
  - disambiguate sendcan and can (useful to know if something sent on sendcan made it to the bus on can->128)
  - print as fixed width table, easier to read
  """

  if route is None:
    lr = live_logreader()
  else:
    lr = LogReader(route, default_mode=ReadMode.RLOG, sort_by_time=True)

  start_mono_time = None
  prev_mono_time = 0

  # include rx addresses
  addrs = addrs + [uds.get_rx_addr_for_tx_addr(addr, rxoffset) for addr in addrs]

  for msg in lr:
    if msg.which() == 'can':
      if start_mono_time is None:
        start_mono_time = msg.logMonoTime

    if msg.which() in ("can", 'sendcan'):
      for can in getattr(msg, msg.which()):
        if can.address in addrs or not len(addrs):
          if msg.logMonoTime != prev_mono_time:
            print()
            prev_mono_time = msg.logMonoTime
          print(f"{msg.which():>7}: rxaddr={can.address}, bus={str(can.src) + ',':<4} {round((msg.logMonoTime - start_mono_time) * 1e-6)} ms, " +
                f"0x{can.dat.hex()}, {can.dat}, {len(can.dat)=}")