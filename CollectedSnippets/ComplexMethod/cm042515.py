def test_only_union_types(self):
    with tempfile.NamedTemporaryFile() as qlog:
      # write valid Event messages
      num_msgs = 100
      with open(qlog.name, "wb") as f:
        f.write(b"".join(capnp_log.Event.new_message().to_bytes() for _ in range(num_msgs)))

      msgs = list(LogReader(qlog.name))
      assert len(msgs) == num_msgs
      [m.which() for m in msgs]

      # append non-union Event message
      event_msg = capnp_log.Event.new_message()
      non_union_bytes = bytearray(event_msg.to_bytes())
      non_union_bytes[event_msg.total_size.word_count * 8] = 0xff  # set discriminant value out of range using Event word offset
      with open(qlog.name, "ab") as f:
        f.write(non_union_bytes)

      # ensure new message is added, but is not a union type
      msgs = list(LogReader(qlog.name))
      assert len(msgs) == num_msgs + 1
      with pytest.raises(capnp.KjException):
        [m.which() for m in msgs]

      # should not be added when only_union_types=True
      msgs = list(LogReader(qlog.name, only_union_types=True))
      assert len(msgs) == num_msgs
      [m.which() for m in msgs]