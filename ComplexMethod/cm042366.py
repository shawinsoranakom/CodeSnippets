def init_pigeon(pigeon: TTYPigeon) -> bool:
  # try initializing a few times
  for _ in range(10):
    try:

      # setup port config
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x03\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00\x00\x1E\x7F")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x00\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x19\x35")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x01\x00\x00\x00\xC0\x08\x00\x00\x00\x08\x07\x00\x01\x00\x01\x00\x00\x00\x00\x00\xF4\x80")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x14\x00\x04\xFF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1D\x85")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x00\x00\x06\x18")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x01\x00\x01\x08\x22")
      pigeon.send_with_ack(b"\xb5\x62\x06\x00\x01\x00\x03\x0A\x24")

      # UBX-CFG-RATE (0x06 0x08)
      pigeon.send_with_ack(b"\xB5\x62\x06\x08\x06\x00\x64\x00\x01\x00\x00\x00\x79\x10")

      # UBX-CFG-NAV5 (0x06 0x24)
      pigeon.send_with_ack(b"\xB5\x62\x06\x24\x24\x00\x05\x00\x04\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x5A\x63")

      # UBX-CFG-ODO (0x06 0x1E)
      pigeon.send_with_ack(b"\xB5\x62\x06\x1E\x14\x00\x00\x00\x00\x00\x01\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x3C\x37")
      pigeon.send_with_ack(b"\xB5\x62\x06\x39\x08\x00\xFF\xAD\x62\xAD\x1E\x63\x00\x00\x83\x0C")
      pigeon.send_with_ack(b"\xB5\x62\x06\x23\x28\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x24")

      # UBX-CFG-NAV5 (0x06 0x24)
      pigeon.send_with_ack(b"\xB5\x62\x06\x24\x00\x00\x2A\x84")
      pigeon.send_with_ack(b"\xB5\x62\x06\x23\x00\x00\x29\x81")
      pigeon.send_with_ack(b"\xB5\x62\x06\x1E\x00\x00\x24\x72")
      pigeon.send_with_ack(b"\xB5\x62\x06\x39\x00\x00\x3F\xC3")

      # UBX-CFG-MSG (set message rate)
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x01\x07\x01\x13\x51")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x02\x15\x01\x22\x70")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x02\x13\x01\x20\x6C")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x0A\x09\x01\x1E\x70")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x0A\x0B\x01\x20\x74")
      pigeon.send_with_ack(b"\xB5\x62\x06\x01\x03\x00\x01\x35\x01\x41\xAD")
      cloudlog.debug("pigeon configured")

      # try restoring almanac backup
      pigeon.send(b"\xB5\x62\x09\x14\x00\x00\x1D\x60")
      restore_status = pigeon.wait_for_backup_restore_status()
      if restore_status == 2:
        cloudlog.warning("almanac backup restored")
      elif restore_status == 3:
        cloudlog.warning("no almanac backup found")
      else:
        cloudlog.error(f"failed to restore almanac backup, status: {restore_status}")

      # sending time to ublox
      if system_time_valid():
        t_now = datetime.now(UTC).replace(tzinfo=None)
        cloudlog.warning("Sending current time to ublox")

        # UBX-MGA-INI-TIME_UTC
        msg = add_ubx_checksum(b"\xB5\x62\x13\x40\x18\x00" + struct.pack("<BBBBHBBBBBxIHxxI",
          0x10,
          0x00,
          0x00,
          0x80,
          t_now.year,
          t_now.month,
          t_now.day,
          t_now.hour,
          t_now.minute,
          t_now.second,
          0,
          30,
          0
        ))
        pigeon.send_with_ack(msg, ack=UBLOX_ASSIST_ACK)

      # try getting AssistNow if we have a token
      token = Params().get('AssistNowToken')
      if token is not None:
        try:
          for msg in get_assistnow_messages(token):
            pigeon.send_with_ack(msg, ack=UBLOX_ASSIST_ACK)
          cloudlog.warning("AssistNow messages sent")
        except Exception:
          cloudlog.warning("failed to get AssistNow messages")

      cloudlog.warning("Pigeon GPS on!")
      break
    except TimeoutError:
      cloudlog.warning("Initialization failed, trying again!")
  else:
    cloudlog.warning("Failed to initialize pigeon")
    return False
  return True