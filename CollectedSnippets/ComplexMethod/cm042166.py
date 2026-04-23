def can_printer(bus=0, init_msgs=None, new_msgs=None, table=False):
  logcan = messaging.sub_sock('can', timeout=10)

  dat = defaultdict(int)
  low_to_high = defaultdict(int)
  high_to_low = defaultdict(int)

  if init_msgs is not None:
    update(init_msgs, bus, dat, low_to_high, high_to_low, quiet=True)

  low_to_high_init = low_to_high.copy()
  high_to_low_init = high_to_low.copy()

  if new_msgs is not None:
    update(new_msgs, bus, dat, low_to_high, high_to_low)
  else:
    # Live mode
    print(f"Waiting for messages on bus {bus}")
    try:
      while 1:
        can_recv = messaging.drain_sock(logcan)
        update(can_recv, bus, dat, low_to_high, high_to_low)
        time.sleep(0.02)
    except KeyboardInterrupt:
      pass

  print("\n\n")
  tables = ""
  for addr in sorted(dat.keys()):
    init = low_to_high_init[addr] & high_to_low_init[addr]
    now = low_to_high[addr] & high_to_low[addr]
    d = now & ~init
    if d == 0:
      continue
    b = d.to_bytes(len(dat[addr]), byteorder='big')

    byts = ''.join([(c if c == '0' else f'{RED}{c}{CLEAR}') for c in str(binascii.hexlify(b))[2:-1]])
    header = f"{hex(addr).ljust(6)}({str(addr).ljust(4)})"
    print(header, byts)
    tables += f"{header}\n"
    tables += can_table(b) + "\n\n"

  if table:
    print(tables)