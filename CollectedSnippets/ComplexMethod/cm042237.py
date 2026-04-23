def test_loopback(self):
    setup_pandad()

    sendcan = messaging.pub_sock('sendcan')
    can = messaging.sub_sock('can', conflate=False, timeout=100)
    sm = messaging.SubMaster(['pandaStates'])
    time.sleep(1)

    n = 200
    for i in range(n):
      print(f"pandad loopback {i}/{n}")

      sent_msgs = send_random_can_messages(sendcan, random.randrange(20, 100))

      sent_loopback = copy.deepcopy(sent_msgs)
      sent_loopback.update({k+128: copy.deepcopy(v) for k, v in sent_msgs.items()})
      sent_total = {k: len(v) for k, v in sent_loopback.items()}
      for _ in range(100 * 5):
        sm.update(0)
        recvd = messaging.drain_sock(can, wait_for_one=True)
        for msg in recvd:
          for m in msg.can:
            key = (m.address, m.dat)
            assert key in sent_loopback[m.src], f"got unexpected msg: {m.src=} {m.address=} {m.dat=}"
            sent_loopback[m.src].discard(key)

        if all(len(v) == 0 for v in sent_loopback.values()):
          break

      # if a set isn't empty, messages got dropped
      pprint(sent_msgs)
      pprint(sent_loopback)
      print({k: len(x) for k, x in sent_loopback.items()})
      print(sum([len(x) for x in sent_loopback.values()]))
      pprint(sm['pandaStates'])  # may drop messages due to RX buffer overflow
      for bus in sent_loopback.keys():
        assert not len(sent_loopback[bus]), f"loop {i}: bus {bus} missing {len(sent_loopback[bus])} out of {sent_total[bus]} messages"