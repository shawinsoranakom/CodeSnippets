def format(self, record):
        artifact_name = getattr(logging.getLogger(record.name), "artifact_name", None)
        if artifact_name is not None:
            artifact_formatter = log_registry.artifact_log_formatters.get(
                artifact_name, None
            )
            if artifact_formatter is not None:
                return artifact_formatter.format(record)

        record.message = record.getMessage()
        record.asctime = self.formatTime(record, "%m%d %H:%M:%S")

        # exception handling - copied from logging.Formatter.format
        s = record.message
        if record.exc_info:
            from torch._dynamo import config

            should_format_exc = config.verbose or artifact_name != "graph_breaks"
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if should_format_exc:
                if not record.exc_text:
                    record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)

        record.rankprefix = ""
        if not self._is_trace and dist.is_available() and dist.is_initialized():
            record.rankprefix = f"[rank{dist.get_rank()}]:"

        record.traceid = ""
        if (
            not self._is_trace
            and (trace_id := torch._guards.CompileContext.current_trace_id())
            is not None
        ):
            record.traceid = f" [{trace_id}]"

        glog_level_to_abbr = {
            "DEBUG": "V",  # V is for VERBOSE in glog
            "INFO": "I",
            "WARNING": "W",
            "ERROR": "E",
            "CRITICAL": "C",
        }

        shortlevel = glog_level_to_abbr.get(record.levelname, record.levelname)

        record.artifactprefix = ""
        if artifact_name is not None:
            record.artifactprefix = f" [__{artifact_name}]"

        filepath = make_module_path_relative(record.pathname)

        if (
            self._trace_id_filter
            and record.traceid.strip() not in self._trace_id_filter
        ):
            return ""

        prefix = (
            f"{record.rankprefix}{shortlevel}{record.asctime}.{int(record.msecs * 1000):06d} {record.process} "
            f"{filepath}:"
            f"{record.lineno}]{record.traceid}{record.artifactprefix}"
        )
        if self._is_trace:
            if s != "":
                raise AssertionError(f"expected empty string for trace, got {s!r}")
            r = f"{prefix} {json.dumps(record.metadata, default=repr)}"
            if record.payload is not None:
                r += "".join(f"\n\t{l}" for l in record.payload.split("\n"))
            return r
        else:
            lines = s.split("\n")
            return "\n".join(f"{prefix} {l}" for l in lines)