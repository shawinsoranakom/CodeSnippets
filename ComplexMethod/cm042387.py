def process_nmea_port_messages(device:str="/dev/ttyUSB1") -> NoReturn:
  while True:
    try:
      with open(device) as nmeaport:
        for line in nmeaport:
          line = line.strip()
          if DEBUG:
            print(line)
          if not line.startswith("$"): # all NMEA messages start with $
            continue
          if not nmea_checksum_ok(line):
            continue

          fields = line.split(",")
          match fields[0]:
            case "$GNCLK":
              # fields at end are reserved (not used)
              gnss_clock = GnssClockNmeaPort(*fields[1:10])
              print(gnss_clock)
            case "$GNMEAS":
              # fields at end are reserved (not used)
              gnss_meas = GnssMeasNmeaPort(*fields[1:14])
              print(gnss_meas)
    except Exception as e:
      print(e)
      sleep(1)