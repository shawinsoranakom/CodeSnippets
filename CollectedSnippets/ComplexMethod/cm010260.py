def emit(self, record) -> None:
        if self.stream is None:
            if self.root_dir is None:
                TRACE_LOG_DIR = "/logs"

                import torch.version as torch_version

                if (
                    hasattr(torch_version, "git_version")
                    and os.getenv("MAST_HPC_JOB_NAME") is None
                ):
                    log.info(
                        "LazyTraceHandler: disabled because not fbcode or conda on mast"
                    )
                elif not torch._utils_internal.justknobs_check("pytorch/trace:enable"):
                    log.info(
                        "LazyTraceHandler: disabled because justknobs_check('pytorch/trace:enable') returned False"
                    )
                elif not os.path.exists(TRACE_LOG_DIR):
                    log.info(
                        "LazyTraceHandler: disabled because %s does not exist",
                        TRACE_LOG_DIR,
                    )
                elif not os.access(TRACE_LOG_DIR, os.W_OK):
                    log.info(
                        "LazyTraceHandler: disabled because %s is not writeable",
                        TRACE_LOG_DIR,
                    )
                else:
                    self.root_dir = TRACE_LOG_DIR

            if self.root_dir is not None:
                os.makedirs(self.root_dir, exist_ok=True)
                ranksuffix = ""
                if dist.is_available() and dist.is_initialized():
                    ranksuffix = f"rank_{dist.get_rank()}_"
                self.stream = tempfile.NamedTemporaryFile(  # noqa: SIM115
                    mode="w+",
                    suffix=".log",
                    prefix=LOG_PREFIX + ranksuffix,
                    dir=self.root_dir,
                    delete=False,
                )
                log.info("LazyTraceHandler: logging to %s", self.stream.name)
                # Log tlparse path via inductor logger so it shows when
                # TORCH_LOGS="inductor" is enabled
                inductor_log = logging.getLogger("torch._inductor")
                inductor_log.info("tlparse raw data: %s", self.stream.name)
                self._pending_log_version = True
            else:
                # We go poof, remove and no-op
                trace_log.removeHandler(self)
                return
        if self.stream:
            super().emit(record)
            if self._pending_log_version:
                self._pending_log_version = False
                _log_torch_version()