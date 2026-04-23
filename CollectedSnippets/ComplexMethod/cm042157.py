def can_printer(bus, max_msg, addr, ascii_decode):
  logcan = messaging.sub_sock('can', addr=addr)

  start = time.monotonic()
  lp = time.monotonic()
  msgs = defaultdict(list)
  while 1:
    can_recv = messaging.drain_sock(logcan, wait_for_one=True)
    for x in can_recv:
      for y in x.can:
        if y.src == bus:
          msgs[y.address].append(y.dat)

    if time.monotonic() - lp > 0.1:
      dd = chr(27) + "[2J"
      dd += f"{time.monotonic() - start:5.2f}\n"
      for _addr in sorted(msgs.keys()):
        a = f"\"{msgs[_addr][-1].decode('ascii', 'backslashreplace')}\"" if ascii_decode else ""
        x = binascii.hexlify(msgs[_addr][-1]).decode('ascii')
        freq = len(msgs[_addr]) / (time.monotonic() - start)
        if max_msg is None or _addr < max_msg:
          dd += f"{_addr:04X}({_addr:4d})({len(msgs[_addr]):6d})({freq:3}dHz) {x.ljust(20)} {a}\n"
      print(dd)
      lp = time.monotonic()