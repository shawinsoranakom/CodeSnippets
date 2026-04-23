def test_RecordIterator(entries, batch, is_live, _gen_events_file):
    """ Test that our :class:`lib.training.tensorboard.RecordIterator` returns expected results """
    keys = list(entries)
    vals = list(entries.values())
    batches = [batch + i for i in range(len(keys))]

    file = _gen_events_file(keys, vals, batches)
    iterator = mod_tb.RecordIterator(file, is_live=is_live)

    results = list(event_pb2.Event.FromString(v) for v in iterator)
    valid = [r for r in results if r.summary.value]

    assert len(valid) == len(keys)
    for entry, key, val, btc in zip(valid, keys, vals, batches):
        assert len(entry.summary.value) == 1
        assert entry.step == btc
        assert entry.summary.value[0].tag == key
        assert np.isclose(entry.summary.value[0].simple_value, val)

    if is_live:
        assert iterator._is_live is True
        assert os.path.getsize(file) == iterator._position  # At end of file
    else:
        assert iterator._is_live is False
        assert iterator._position == 0