def cmd_download(args):
  url = args.url
  use_cache = not args.no_cache

  if use_cache:
    local_path = cache_file_path(url)
    if os.path.exists(local_path):
      sys.stdout.write(local_path + "\n")
      sys.stdout.flush()
      return

  try:
    # Stream the file in a single HTTP request instead of making
    # a separate Range request per chunk (which was very slow).
    pool = URLFile.pool_manager()
    r = pool.request("GET", url, preload_content=False)
    if r.status not in (200, 206):
      sys.stderr.write(f"ERROR:HTTP {r.status}\n")
      sys.stderr.flush()
      sys.exit(1)

    total = int(r.headers.get('content-length', 0))
    if total <= 0:
      sys.stderr.write("ERROR:File not found or empty\n")
      sys.stderr.flush()
      sys.exit(1)

    os.makedirs(Paths.download_cache_root(), exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=Paths.download_cache_root())
    try:
      downloaded = 0
      chunk_size = 1024 * 1024
      with os.fdopen(tmp_fd, 'wb') as f:
        for data in r.stream(chunk_size):
          f.write(data)
          downloaded += len(data)
          sys.stderr.write(f"PROGRESS:{downloaded}:{total}\n")
          sys.stderr.flush()

      if use_cache:
        shutil.move(tmp_path, local_path)
        sys.stdout.write(local_path + "\n")
      else:
        sys.stdout.write(tmp_path + "\n")
    except Exception:
      try:
        os.unlink(tmp_path)
      except OSError:
        pass
      raise
    finally:
      r.release_conn()

  except Exception as e:
    sys.stderr.write(f"ERROR:{e}\n")
    sys.stderr.flush()
    sys.exit(1)

  sys.stdout.flush()