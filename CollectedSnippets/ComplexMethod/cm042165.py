def update(msgs, bus, dat, low_to_high, high_to_low, quiet=False):
  for x in msgs:
    if x.which() != 'can':
      continue

    for y in x.can:
      if y.src == bus:
        dat[y.address] = y.dat

        i = int.from_bytes(y.dat, byteorder='big')
        l_h = low_to_high[y.address]
        h_l = high_to_low[y.address]

        change = None
        if (i | l_h) != l_h:
          low_to_high[y.address] = i | l_h
          change = "+"

        if (~i | h_l) != h_l:
          high_to_low[y.address] = ~i | h_l
          change = "-"

        if change and not quiet:
          print(f"{time.monotonic():.2f}\t{hex(y.address)} ({y.address})\t{change}{binascii.hexlify(y.dat)}")