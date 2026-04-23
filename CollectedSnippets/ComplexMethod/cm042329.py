def upload_handler(end_event: threading.Event) -> None:
  sm = messaging.SubMaster(['deviceState'])
  tid = threading.get_ident()

  while not end_event.is_set():
    cur_upload_items[tid] = None

    try:
      cur_upload_items[tid] = item = replace(upload_queue.get(timeout=1), current=True)

      if item.id in cancelled_uploads:
        cancelled_uploads.remove(item.id)
        continue

      # Remove item if too old
      age = datetime.now() - datetime.fromtimestamp(item.created_at / 1000)
      if age.total_seconds() > MAX_AGE:
        cloudlog.event("athena.upload_handler.expired", item=item, error=True)
        continue

      # Check if uploading over metered connection is allowed
      sm.update(0)
      metered = sm['deviceState'].networkMetered
      network_type = sm['deviceState'].networkType.raw
      if metered and (not item.allow_cellular):
        retry_upload(tid, end_event, False)
        continue

      try:
        fn = item.path
        try:
          sz = os.path.getsize(fn)
        except OSError:
          sz = -1

        cloudlog.event("athena.upload_handler.upload_start", fn=fn, sz=sz, network_type=network_type, metered=metered, retry_count=item.retry_count)

        with _do_upload(item, partial(cb, sm, item, tid, end_event)) as response:
          if response.status_code not in (200, 201, 401, 403, 412):
            cloudlog.event("athena.upload_handler.retry", status_code=response.status_code, fn=fn, sz=sz, network_type=network_type, metered=metered)
            retry_upload(tid, end_event)
          else:
            cloudlog.event("athena.upload_handler.success", fn=fn, sz=sz, network_type=network_type, metered=metered)

        UploadQueueCache.cache(upload_queue)
      except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError):
        cloudlog.event("athena.upload_handler.timeout", fn=fn, sz=sz, network_type=network_type, metered=metered)
        retry_upload(tid, end_event)
      except AbortTransferException:
        cloudlog.event("athena.upload_handler.abort", fn=fn, sz=sz, network_type=network_type, metered=metered)
        retry_upload(tid, end_event, False)

    except queue.Empty:
      pass
    except Exception:
      cloudlog.exception("athena.upload_handler.exception")