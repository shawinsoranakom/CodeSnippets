def migrate_longitudinalPlan(msgs):
  ops = []

  needs_migration = all(msg.longitudinalPlan.aTarget == 0.0 for _, msg in msgs if msg.which() == 'longitudinalPlan')
  CP = next((m.carParams for _, m in msgs if m.which() == 'carParams'), None)
  if not needs_migration or CP is None:
    return [], [], []

  for index, msg in msgs:
    if msg.which() != 'longitudinalPlan':
      continue
    new_msg = msg.as_builder()
    a_target, should_stop = get_accel_from_plan(msg.longitudinalPlan.speeds, msg.longitudinalPlan.accels, CONTROL_N_T_IDX)
    new_msg.longitudinalPlan.aTarget, new_msg.longitudinalPlan.shouldStop = float(a_target), bool(should_stop)
    ops.append((index, new_msg.as_reader()))
  return ops, [], []