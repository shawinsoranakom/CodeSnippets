def write_csv_when_exception(args, name: str, status: str, device=None):
    print(status)
    placeholder_batch_size = 0
    devices = [device] if device is not None else args.devices
    if args.accuracy:
        headers = ["dev", "name", "batch_size", "accuracy"]
        rows = [[device, name, placeholder_batch_size, status] for device in devices]
    elif args.performance:
        headers = ["dev", "name", "batch_size", "speedup", "abs_latency"]
        rows = [[device, name, placeholder_batch_size, 0.0, 0.0] for device in devices]
    else:
        headers = []
        rows = [[device, name, placeholder_batch_size, 0.0] for device in devices]

    for row in rows:
        write_outputs(output_filename, headers, row)