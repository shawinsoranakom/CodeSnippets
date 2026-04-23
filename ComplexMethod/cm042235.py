def main() -> None:
  # signal pandad to close the relay and exit
  def signal_handler(signum, frame):
    cloudlog.info(f"Caught signal {signum}, exiting")
    nonlocal do_exit
    do_exit = True
    if process is not None:
      process.send_signal(signal.SIGINT)

  process = None
  do_exit = False
  signal.signal(signal.SIGINT, signal_handler)

  count = 0
  first_run = True
  params = Params()
  no_internal_panda_count = 0

  while not do_exit:
    try:
      count += 1
      cloudlog.event("pandad.flash_and_connect", count=count)
      params.remove("PandaSignatures")

      # Handle missing internal panda
      if no_internal_panda_count > 0:
        if no_internal_panda_count == 3:
          cloudlog.info("No pandas found, putting internal panda into DFU")
          HARDWARE.recover_internal_panda()
        else:
          cloudlog.info("No pandas found, resetting internal panda")
          HARDWARE.reset_internal_panda()
        time.sleep(3)  # wait to come back up

      # Flash all Pandas in DFU mode
      dfu_serials = PandaDFU.list()
      if len(dfu_serials) > 0:
        for serial in dfu_serials:
          cloudlog.info(f"Panda in DFU mode found, flashing recovery {serial}")
          PandaDFU(serial).recover()
        time.sleep(1)

      panda_serials = Panda.list()
      if len(panda_serials) == 0:
        no_internal_panda_count += 1
        continue

      cloudlog.info(f"{len(panda_serials)} panda(s) found, connecting - {panda_serials}")

      # Flash the first panda
      panda_serial = panda_serials[0]
      panda = flash_panda(panda_serial)

      # Ensure internal panda is present if expected
      if HARDWARE.has_internal_panda() and not panda.is_internal():
        cloudlog.error("Internal panda is missing, trying again")
        no_internal_panda_count += 1
        continue
      no_internal_panda_count = 0

      # log panda fw version
      params.put("PandaSignatures", panda.get_signature())

      # check health for lost heartbeat
      health = panda.health()
      if health["heartbeat_lost"]:
        params.put_bool("PandaHeartbeatLost", True)
        cloudlog.event("heartbeat lost", deviceState=health, serial=panda.get_usb_serial())
      if health["som_reset_triggered"]:
        params.put_bool("PandaSomResetTriggered", True)
        cloudlog.event("panda.som_reset_triggered", health=health, serial=panda.get_usb_serial())

      if first_run:
        # reset panda to ensure we're in a good state
        cloudlog.info(f"Resetting panda {panda.get_usb_serial()}")
        panda.reset(reconnect=True)

      panda.close()
    # TODO: wrap all panda exceptions in a base panda exception
    except (usb1.USBErrorNoDevice, usb1.USBErrorPipe):
      # a panda was disconnected while setting everything up. let's try again
      cloudlog.exception("Panda USB exception while setting up")
      continue
    except PandaProtocolMismatch:
      cloudlog.exception("pandad.protocol_mismatch")
      continue
    except Exception:
      cloudlog.exception("pandad.uncaught_exception")
      continue

    first_run = False

    # run pandad with all connected serials as arguments
    os.environ['MANAGER_DAEMON'] = 'pandad'
    process = subprocess.Popen(["./pandad", panda_serial], cwd=os.path.join(BASEDIR, "selfdrive/pandad"))
    process.wait()