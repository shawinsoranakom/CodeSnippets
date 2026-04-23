def report_tombstone_apport(fn):
  f_size = os.path.getsize(fn)
  if f_size > MAX_SIZE:
    cloudlog.error(f"Tombstone {fn} too big, {f_size}. Skipping...")
    return

  message = ""  # One line description of the crash
  contents = ""  # Full file contents without coredump
  path = ""  # File path relative to openpilot directory

  proc_maps = False

  with open(fn) as f:
    for line in f:
      if "CoreDump" in line:
        break
      elif "ProcMaps" in line:
        proc_maps = True
      elif "ProcStatus" in line:
        proc_maps = False

      if not proc_maps:
        contents += line

      if "ExecutablePath" in line:
        path = line.strip().split(': ')[-1]
        path = path.replace('/data/openpilot/', '')
        message += path
      elif "Signal" in line:
        message += " - " + line.strip()

        try:
          sig_num = int(line.strip().split(': ')[-1])
          message += " (" + signal.Signals(sig_num).name + ")"
        except ValueError:
          pass

  stacktrace = get_apport_stacktrace(fn)
  stacktrace_s = stacktrace.split('\n')
  crash_function = "No stacktrace"

  if len(stacktrace_s) > 2:
    found = False

    # Try to find first entry in openpilot, fall back to first line
    for line in stacktrace_s:
      if "at selfdrive/" in line:
        crash_function = line
        found = True
        break

    if not found:
      crash_function = stacktrace_s[1]

    # Remove arguments that can contain pointers to make sentry one-liner unique
    crash_function = " ".join(x for x in crash_function.split(' ')[1:] if not x.startswith('0x'))
    crash_function = re.sub(r'\(.*?\)', '', crash_function)

  contents = stacktrace + "\n\n" + contents
  message = message + " - " + crash_function
  sentry.report_tombstone(fn, message, contents)

  # Copy crashlog to upload folder
  clean_path = path.replace('/', '_')
  date = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")

  build_metadata = get_build_metadata()

  new_fn = f"{date}_{(build_metadata.openpilot.git_commit or 'nocommit')[:8]}_{safe_fn(clean_path)}"[:MAX_TOMBSTONE_FN_LEN]

  crashlog_dir = os.path.join(Paths.log_root(), "crash")
  os.makedirs(crashlog_dir, exist_ok=True)

  # Files could be on different filesystems, copy, then delete
  shutil.copy(fn, os.path.join(crashlog_dir, new_fn))

  try:
    os.remove(fn)
  except PermissionError:
    pass