def test_list_data_directory(self):
    route = '2021-03-29--13-32-47'
    segments = [0, 1, 2, 3, 11]

    filenames = ['qlog.zst', 'qcamera.ts', 'rlog.zst', 'fcamera.hevc', 'ecamera.hevc', 'dcamera.hevc']
    files = [f'{route}--{s}/{f}' for s in segments for f in filenames]
    for file in files:
      self._create_file(file)

    resp = dispatcher["listDataDirectory"]()
    assert resp, 'list empty!'
    assert len(resp) == len(files)

    resp = dispatcher["listDataDirectory"](f'{route}--123')
    assert len(resp) == 0

    prefix = f'{route}'
    expected = list(filter(lambda f: f.startswith(prefix), files))
    resp = dispatcher["listDataDirectory"](prefix)
    assert resp, 'list empty!'
    assert len(resp) == len(expected)

    prefix = f'{route}--1'
    expected = list(filter(lambda f: f.startswith(prefix), files))
    resp = dispatcher["listDataDirectory"](prefix)
    assert resp, 'list empty!'
    assert len(resp) == len(expected)

    prefix = f'{route}--1/'
    expected = list(filter(lambda f: f.startswith(prefix), files))
    resp = dispatcher["listDataDirectory"](prefix)
    assert resp, 'list empty!'
    assert len(resp) == len(expected)

    prefix = f'{route}--1/q'
    expected = list(filter(lambda f: f.startswith(prefix), files))
    resp = dispatcher["listDataDirectory"](prefix)
    assert resp, 'list empty!'
    assert len(resp) == len(expected)