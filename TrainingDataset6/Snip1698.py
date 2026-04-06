def prepare(self, monkeypatch):
        monkeypatch.setattr('thefuck.output_readers.rerun._wait_output',
                            lambda *_: True)