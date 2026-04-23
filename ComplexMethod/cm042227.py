def replay_process(
  cfg: ProcessConfig | Iterable[ProcessConfig], lr: LogIterable, frs: dict[str, FrameReader] | None = None,
  fingerprint: str | None = None, return_all_logs: bool = False, custom_params: dict[str, Any] | None = None,
  captured_output_store: dict[str, dict[str, str]] | None = None, disable_progress: bool = False
) -> list[capnp._DynamicStructReader]:
  if isinstance(cfg, Iterable):
    cfgs = list(cfg)
  else:
    cfgs = [cfg]

  all_msgs = migrate_all(lr,
                         manager_states=True,
                         panda_states=any("pandaStates" in cfg.pubs for cfg in cfgs),
                         camera_states=any(len(cfg.vision_pubs) != 0 for cfg in cfgs))
  process_logs = _replay_multi_process(cfgs, all_msgs, frs, fingerprint, custom_params, captured_output_store, disable_progress)

  if return_all_logs:
    keys = {m.which() for m in process_logs}
    modified_logs = [m for m in all_msgs if m.which() not in keys]
    modified_logs.extend(process_logs)
    modified_logs.sort(key=lambda m: int(m.logMonoTime))
    log_msgs = modified_logs
  else:
    log_msgs = process_logs

  return log_msgs