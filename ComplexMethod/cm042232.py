def start(
    self, params_config: dict[str, Any], environ_config: dict[str, Any],
    all_msgs: LogIterable, frs: dict[str, FrameReader] | None,
    fingerprint: str | None, capture_output: bool
  ):
    with self.prefix as p:
      self.prefix.create_dirs()
      self._setup_env(params_config, environ_config)

      if self.cfg.config_callback is not None:
        params = Params()
        self.cfg.config_callback(params, self.cfg, all_msgs)

      self.rc = ReplayContext(self.cfg)
      self.rc.open_context()

      self.pm = messaging.PubMaster(self.cfg.pubs)
      self.sockets = [messaging.sub_sock(s, timeout=100) for s in self.cfg.subs]

      if len(self.cfg.vision_pubs) != 0:
        assert frs is not None
        self._setup_vision_ipc(all_msgs, frs)
        assert self.vipc_server is not None

      if capture_output:
        self.capture = ProcessOutputCapture(self.cfg.proc_name, p.prefix)

      self._start_process()

      if self.cfg.init_callback is not None:
        self.cfg.init_callback(self.rc, self.pm, all_msgs, fingerprint)