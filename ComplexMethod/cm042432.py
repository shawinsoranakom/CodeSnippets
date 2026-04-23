def trace_log_callback(log_level, text, args):
      try:
        text_addr = int(rl.ffi.cast("uintptr_t", text))
        args_addr = int(rl.ffi.cast("uintptr_t", args))
        text_libc = ffi_libc.cast("char *", text_addr)
        args_libc = ffi_libc.cast("void *", args_addr)

        out = ffi_libc.new("char **")
        if libc.vasprintf(out, text_libc, args_libc) >= 0 and out[0] != ffi_libc.NULL:
          text_str = ffi_libc.string(out[0]).decode("utf-8", "replace")
          libc.free(out[0])
        else:
          text_str = rl.ffi.string(text).decode("utf-8", "replace")
      except Exception as e:
        text_str = f"[Log decode error: {e}]"

      if log_level == rl.TraceLogLevel.LOG_ERROR:
        cloudlog.error(f"raylib: {text_str}")
      elif log_level == rl.TraceLogLevel.LOG_WARNING:
        cloudlog.warning(f"raylib: {text_str}")
      elif log_level == rl.TraceLogLevel.LOG_INFO:
        cloudlog.info(f"raylib: {text_str}")
      elif log_level == rl.TraceLogLevel.LOG_DEBUG:
        cloudlog.debug(f"raylib: {text_str}")
      else:
        cloudlog.error(f"raylib: Unknown level {log_level}: {text_str}")