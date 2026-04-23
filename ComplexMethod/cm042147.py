def test_send(self):
    socks = random_socks()
    pm = messaging.PubMaster(socks)
    sub_socks = {s: messaging.sub_sock(s, conflate=True, timeout=1000) for s in socks}
    zmq_sleep()

    # PubMaster accepts either a capnp msg builder or bytes
    for capnp in [True, False]:
      for i in range(100):
        sock = socks[i % len(socks)]

        if capnp:
          try:
            msg = messaging.new_message(sock)
          except Exception:
            msg = messaging.new_message(sock, random.randrange(50))
        else:
          msg = random_bytes()

        pm.send(sock, msg)
        recvd = sub_socks[sock].receive()

        if capnp:
          msg.clear_write_flag()
          msg = msg.to_bytes()
        assert msg == recvd, i