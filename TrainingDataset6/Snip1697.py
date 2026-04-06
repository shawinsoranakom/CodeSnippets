def Popen(self, monkeypatch):
        Popen = Mock()
        Popen.return_value.stdout.read.return_value = b'output'
        monkeypatch.setattr('thefuck.output_readers.rerun.Popen', Popen)
        return Popen