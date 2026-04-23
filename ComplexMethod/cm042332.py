def ws_recv(ws: WebSocket, end_event: threading.Event) -> None:
  last_ping = int(time.monotonic() * 1e9)
  while not end_event.is_set():
    try:
      opcode, data = ws.recv_data(control_frame=True)
      if opcode in (ABNF.OPCODE_TEXT, ABNF.OPCODE_BINARY):
        if opcode == ABNF.OPCODE_TEXT:
          data = data.decode("utf-8")
        recv_queue.put_nowait(data)
      elif opcode == ABNF.OPCODE_PING:
        last_ping = int(time.monotonic() * 1e9)
        Params().put("LastAthenaPingTime", last_ping)
    except WebSocketTimeoutException:
      ns_since_last_ping = int(time.monotonic() * 1e9) - last_ping
      if ns_since_last_ping > RECONNECT_TIMEOUT_S * 1e9:
        cloudlog.exception("athenad.ws_recv.timeout")
        end_event.set()
    except Exception:
      cloudlog.exception("athenad.ws_recv.exception")
      end_event.set()