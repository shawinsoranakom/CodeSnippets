def log_handler(end_event: threading.Event) -> None:
  if PC:
    return

  log_files = []
  last_scan = 0.
  while not end_event.is_set():
    try:
      curr_scan = time.monotonic()
      if curr_scan - last_scan > 10:
        log_files = get_logs_to_send_sorted()
        last_scan = curr_scan

      # send one log
      curr_log = None
      if len(log_files) > 0:
        log_entry = log_files.pop() # newest log file
        cloudlog.debug(f"athena.log_handler.forward_request {log_entry}")
        try:
          curr_time = int(time.time())  # noqa: TID251
          log_path = os.path.join(Paths.swaglog_root(), log_entry)
          setxattr(log_path, LOG_ATTR_NAME, int.to_bytes(curr_time, 4, sys.byteorder))
          with open(log_path) as f:
            jsonrpc = {
              "method": "forwardLogs",
              "params": {
                "logs": f.read()
              },
              "jsonrpc": "2.0",
              "id": log_entry
            }
            low_priority_send_queue.put_nowait(json.dumps(jsonrpc))
            curr_log = log_entry
        except OSError:
          pass  # file could be deleted by log rotation

      # wait for response up to ~100 seconds
      # always read queue at least once to process any old responses that arrive
      for _ in range(100):
        if end_event.is_set():
          break
        try:
          log_resp = json.loads(log_recv_queue.get(timeout=1))
          log_entry = log_resp.get("id")
          log_success = "result" in log_resp and log_resp["result"].get("success")
          cloudlog.debug(f"athena.log_handler.forward_response {log_entry} {log_success}")
          if log_entry and log_success:
            log_path = os.path.join(Paths.swaglog_root(), log_entry)
            try:
              setxattr(log_path, LOG_ATTR_NAME, LOG_ATTR_VALUE_MAX_UNIX_TIME)
            except OSError:
              pass  # file could be deleted by log rotation
          if curr_log == log_entry:
            break
        except queue.Empty:
          if curr_log is None:
            break

    except Exception:
      cloudlog.exception("athena.log_handler.exception")