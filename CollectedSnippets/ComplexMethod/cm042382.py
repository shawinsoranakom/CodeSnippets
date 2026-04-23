def main() -> None:
  params = Params()

  if params.get_bool("DisableUpdates"):
    cloudlog.warning("updates are disabled by the DisableUpdates param")
    exit(0)

  with open(LOCK_FILE, 'w') as ov_lock_fd:
    try:
      fcntl.flock(ov_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as e:
      raise RuntimeError("couldn't get overlay lock; is another instance running?") from e

    # Set low io priority
    proc = psutil.Process()
    if psutil.LINUX:
      proc.ionice(psutil.IOPRIO_CLASS_BE, value=7)

    # Check if we just performed an update
    if Path(os.path.join(STAGING_ROOT, "old_openpilot")).is_dir():
      cloudlog.event("update installed")

    if not params.get("InstallDate"):
      t = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
      params.put("InstallDate", t)

    updater = Updater()
    update_failed_count = 0 # TODO: Load from param?
    wait_helper = WaitTimeHelper()

    # invalidate old finalized update
    set_consistent_flag(False)

    # set initial state
    params.put("UpdaterState", "idle")

    # Run the update loop
    first_run = True
    while True:
      wait_helper.ready_event.clear()

      # Attempt an update
      exception = None
      try:
        # TODO: reuse overlay from previous updated instance if it looks clean
        init_overlay()

        # ensure we have some params written soon after startup
        updater.set_params(False, update_failed_count, exception)

        if not system_time_valid() or first_run:
          first_run = False
          wait_helper.sleep(60)
          continue

        update_failed_count += 1

        # check for update
        params.put("UpdaterState", "checking...")
        updater.check_for_update()

        # download update
        last_fetch = params.get("UpdaterLastFetchTime")
        timed_out = last_fetch is None or (datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - last_fetch > datetime.timedelta(days=3))
        user_requested_fetch = wait_helper.user_request == UserRequest.FETCH
        if params.get_bool("NetworkMetered") and not timed_out and not user_requested_fetch:
          cloudlog.info("skipping fetch, connection metered")
        elif wait_helper.user_request == UserRequest.CHECK:
          cloudlog.info("skipping fetch, only checking")
        else:
          updater.fetch_update()
          write_time_to_param(params, "UpdaterLastFetchTime")
        update_failed_count = 0
      except subprocess.CalledProcessError as e:
        cloudlog.event(
          "update process failed",
          cmd=e.cmd,
          output=e.output,
          returncode=e.returncode
        )
        exception = f"command failed: {e.cmd}\n{e.output}"
        OVERLAY_INIT.unlink(missing_ok=True)
      except Exception as e:
        cloudlog.exception("uncaught updated exception, shouldn't happen")
        exception = str(e)
        OVERLAY_INIT.unlink(missing_ok=True)

      try:
        params.put("UpdaterState", "idle")
        update_successful = (update_failed_count == 0)
        updater.set_params(update_successful, update_failed_count, exception)
      except Exception:
        cloudlog.exception("uncaught updated exception while setting params, shouldn't happen")

      # infrequent attempts if we successfully updated recently
      wait_helper.user_request = UserRequest.NONE
      wait_helper.sleep(5*60 if update_failed_count > 0 else 1.5*60*60)