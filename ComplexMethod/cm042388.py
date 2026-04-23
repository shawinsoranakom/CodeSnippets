def main() -> NoReturn:
  from openpilot.common.gpio import gpio_init, gpio_set
  from openpilot.system.hardware.tici.pins import GPIO
  from openpilot.system.qcomgpsd.qcomgpsd import at_cmd

  try:
    check_output(["pidof", "qcomgpsd"])
    print("qcomgpsd is running, please kill openpilot before running this script! (aborted)")
    sys.exit(1)
  except CalledProcessError as e:
    if e.returncode != 1: # 1 == no process found (pandad not running)
      raise e

  print("power up antenna ...")
  gpio_init(GPIO.GNSS_PWR_EN, True)
  gpio_set(GPIO.GNSS_PWR_EN, True)

  if b"+QGPS: 0" not in (at_cmd("AT+QGPS?") or b""):
    print("stop location tracking ...")
    at_cmd("AT+QGPSEND")

  if b'+QGPSCFG: "outport",usbnmea' not in (at_cmd('AT+QGPSCFG="outport"') or b""):
    print("configure outport ...")
    at_cmd('AT+QGPSCFG="outport","usbnmea"') # usbnmea = /dev/ttyUSB1

  if b'+QGPSCFG: "gnssrawdata",3,0' not in (at_cmd('AT+QGPSCFG="gnssrawdata"') or b""):
    print("configure gnssrawdata ...")
    # AT+QGPSCFG="gnssrawdata",<constellation-mask>,<port>'
    # <constellation-mask> values:
    # 0x01 = GPS
    # 0x02 = GLONASS
    # 0x04 = BEIDOU
    # 0x08 = GALILEO
    # 0x10 = QZSS
    # <port> values:
    # 0 = NMEA port
    # 1 = AT port
    at_cmd('AT+QGPSCFG="gnssrawdata",3,0') # enable all constellations, output data to NMEA port
    print("rebooting ...")
    at_cmd('AT+CFUN=1,1')
    print("re-run this script when it is back up")
    sys.exit(2)

  print("starting location tracking ...")
  at_cmd("AT+QGPS=1")

  process_nmea_port_messages()