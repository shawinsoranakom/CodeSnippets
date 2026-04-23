def parse_args():
  parser = ArgumentParser(description="Direct clip renderer")
  parser.add_argument("route", nargs="?", help="Route ID (dongle/route or dongle/route/start/end)")
  parser.add_argument("-s", "--start", type=int, help="Start time in seconds")
  parser.add_argument("-e", "--end", type=int, help="End time in seconds")
  parser.add_argument("-o", "--output", default="output.mp4", help="Output file path")
  parser.add_argument("-d", "--data-dir", help="Local directory with route data")
  parser.add_argument("-t", "--title", help="Title overlay text")
  parser.add_argument("-f", "--file-size", type=float, default=9.0, help="Target file size in MB")
  parser.add_argument("-x", "--speed", type=int, default=1, help="Speed multiplier")
  parser.add_argument("--demo", action="store_true", help="Use demo route with default timing")
  parser.add_argument("--big", action="store_true", help="Use big UI (2160x1080)")
  parser.add_argument("--qcam", action="store_true", help="Use qcamera instead of fcamera")
  parser.add_argument("--windowed", action="store_true", help="Show window")
  parser.add_argument("--no-metadata", action="store_true", help="Disable metadata overlay")
  parser.add_argument("--no-time-overlay", action="store_true", help="Disable time overlay")
  args = parser.parse_args()

  if args.demo:
    args.route, args.start, args.end = args.route or DEMO_ROUTE, args.start or DEMO_START, args.end or DEMO_END
  elif not args.route:
    parser.error("route is required (or use --demo)")

  if args.route and args.route.count('/') == 3:
    parts = args.route.split('/')
    args.route, args.start, args.end = '/'.join(parts[:2]), args.start or int(parts[2]), args.end or int(parts[3])

  if args.start is None or args.end is None:
    parser.error("--start and --end are required")
  if args.end <= args.start:
    parser.error(f"end ({args.end}) must be greater than start ({args.start})")
  return args