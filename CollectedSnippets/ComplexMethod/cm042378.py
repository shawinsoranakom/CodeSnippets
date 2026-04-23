def test_qlog(self):
    qlog_services = [s for s in CEREAL_SERVICES if SERVICE_LIST[s].decimation is not None]
    no_qlog_services = [s for s in CEREAL_SERVICES if SERVICE_LIST[s].decimation is None]

    services = random.sample(qlog_services, random.randint(2, min(10, len(qlog_services)))) + \
               random.sample(no_qlog_services, random.randint(2, min(10, len(no_qlog_services))))
    sent_msgs = self._publish_random_messages(services)

    qlog_path = os.path.join(self._get_latest_log_dir(), "qlog.zst")
    lr = list(LogReader(qlog_path))

    # check initData and sentinel
    self._check_init_data(lr)
    self._check_sentinel(lr, True)

    recv_msgs = defaultdict(list)
    for m in lr:
      recv_msgs[m.which()].append(m)

    for s, msgs in sent_msgs.items():
      recv_cnt = len(recv_msgs[s])

      if s in no_qlog_services:
        # check services with no specific decimation aren't in qlog
        assert recv_cnt == 0, f"got {recv_cnt} {s} msgs in qlog"
      else:
        # check logged message count matches decimation
        expected_cnt = (len(msgs) - 1) // SERVICE_LIST[s].decimation + 1
        assert recv_cnt == expected_cnt, f"expected {expected_cnt} msgs for {s}, got {recv_cnt}"