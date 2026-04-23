def migrate(lr: LogIterable, migration_funcs: list[MigrationFunc]):
  lr = list(lr)
  grouped = defaultdict(list)
  for i, msg in enumerate(lr):
    grouped[msg.which()].append(i)

  replace_ops, add_ops, del_ops = [], [], []
  for migration in migration_funcs:
    assert hasattr(migration, "inputs") and hasattr(migration, "product"), "Migration functions must use @migration decorator"
    if migration.product in grouped: # skip if product already exists
      continue

    sorted_indices = sorted(ii for i in cast(list[str], migration.inputs) for ii in grouped.get(i, []))
    msg_gen = [(i, lr[i]) for i in sorted_indices]
    r_ops, a_ops, d_ops = migration(msg_gen)
    replace_ops.extend(r_ops)
    add_ops.extend(a_ops)
    del_ops.extend(d_ops)

  for index, msg in replace_ops:
    lr[index] = msg
  for index in sorted(del_ops, reverse=True):
    del lr[index]
  for msg in add_ops:
    lr.append(msg)
  lr = sorted(lr, key=lambda x: x.logMonoTime)

  return lr