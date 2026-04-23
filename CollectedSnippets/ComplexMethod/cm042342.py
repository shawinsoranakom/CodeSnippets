def hw_state_thread(end_event, hw_queue):
  """Handles non critical hardware state, and sends over queue"""
  count = 0
  prev_hw_state = None

  modem_version = None
  modem_configured = False
  modem_missing_count = 0
  modem_restart_count = 0

  while not end_event.is_set():
    # these are expensive calls. update every 10s
    if (count % int(10. / DT_HW)) == 0:
      try:
        network_type = HARDWARE.get_network_type()
        modem_temps = HARDWARE.get_modem_temperatures()
        if len(modem_temps) == 0 and prev_hw_state is not None:
          modem_temps = prev_hw_state.modem_temps

        # Log modem version once
        if AGNOS and (modem_version is None):
          modem_version = HARDWARE.get_modem_version()

          if modem_version is not None:
            cloudlog.event("modem version", version=modem_version)

        if AGNOS and modem_restart_count < 3 and HARDWARE.get_modem_version() is None:
          # TODO: we may be able to remove this with a MM update
          # ModemManager's probing on startup can fail
          # rarely, restart the service to probe again.
          # Also, AT commands sometimes timeout resulting in ModemManager not
          # trying to use this modem anymore.
          modem_missing_count += 1
          if (modem_missing_count % 4) == 0:
            modem_restart_count += 1
            cloudlog.event("restarting ModemManager")
            os.system("sudo systemctl restart --no-block ModemManager")

        tx, rx = HARDWARE.get_modem_data_usage()

        hw_state = HardwareState(
          network_type=network_type,
          network_info=HARDWARE.get_network_info(),
          network_strength=HARDWARE.get_network_strength(network_type),
          network_stats={'wwanTx': tx, 'wwanRx': rx},
          network_metered=HARDWARE.get_network_metered(network_type),
          modem_temps=modem_temps,
        )

        try:
          hw_queue.put_nowait(hw_state)
        except queue.Full:
          pass

        if not modem_configured and HARDWARE.get_modem_version() is not None:
          cloudlog.warning("configuring modem")
          HARDWARE.configure_modem()
          modem_configured = True

        prev_hw_state = hw_state
      except Exception:
        cloudlog.exception("Error getting hardware state")

    count += 1
    time.sleep(DT_HW)