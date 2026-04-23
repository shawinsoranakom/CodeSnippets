def test_init_state(self):
    socks = random_socks()
    sm = messaging.SubMaster(socks)
    assert sm.frame == -1
    assert not any(sm.updated.values())
    assert not any(sm.seen.values())
    on_demand = {s: SERVICE_LIST[s].frequency <= 1e-5 for s in sm.services}
    assert all(sm.alive[s] == sm.valid[s] == sm.freq_ok[s] == on_demand[s] for s in sm.services)
    assert all(t == 0. for t in sm.recv_time.values())
    assert all(f == 0 for f in sm.recv_frame.values())
    assert all(t == 0 for t in sm.logMonoTime.values())

    for p in [sm.updated, sm.recv_time, sm.recv_frame, sm.alive,
              sm.sock, sm.data, sm.logMonoTime, sm.valid]:
      assert len(cast(Sized, p)) == len(socks)