def _setup_env(self, params_config: dict[str, Any], environ_config: dict[str, Any]):
    for k, v in environ_config.items():
      if len(v) != 0:
        os.environ[k] = v
      elif k in os.environ:
        del os.environ[k]

    os.environ["PROC_NAME"] = self.cfg.proc_name
    if self.cfg.simulation:
      os.environ["SIMULATION"] = "1"
    elif "SIMULATION" in os.environ:
      del os.environ["SIMULATION"]

    params = Params()
    for k, v in params_config.items():
      if isinstance(v, bool):
        params.put_bool(k, v)
      else:
        params.put(k, v)

    self.environ_config = environ_config