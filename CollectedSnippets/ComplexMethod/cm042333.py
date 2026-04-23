def ws_manage(ws: WebSocket, end_event: threading.Event) -> None:
  params = Params()
  onroad_prev = None
  sock = ws.sock

  while True:
    onroad = params.get_bool("IsOnroad")
    if onroad != onroad_prev:
      onroad_prev = onroad

      if sock is not None:
        # While not sending data, onroad, we can expect to time out in 7 + (7 * 2) = 21s
        #                         offroad, we can expect to time out in 30 + (10 * 3) = 60s
        # FIXME: TCP_USER_TIMEOUT is effectively 2x for some reason (32s), so it's mostly unused
        if sys.platform == 'linux':
          sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_USER_TIMEOUT, 16000 if onroad else 0)
          sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 7 if onroad else 30)
        elif sys.platform == 'darwin':
          sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, 7 if onroad else 30)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 7 if onroad else 10)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2 if onroad else 3)

    if end_event.wait(5):
      break