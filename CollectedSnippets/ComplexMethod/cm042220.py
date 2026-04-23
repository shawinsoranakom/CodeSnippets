def migrate_deviceState(msgs):
  init_data = next((m.initData for _, m in msgs if m.which() == 'initData'), None)
  device_state = next((m.deviceState for _, m in msgs if m.which() == 'deviceState'), None)
  if init_data is None or device_state is None:
    return [], [], []

  ops = []
  for i, msg in msgs:
    if msg.which() == 'deviceState':
      n = msg.as_builder()
      n.deviceState.deviceType = init_data.deviceType
      ops.append((i, n.as_reader()))
  return ops, [], []