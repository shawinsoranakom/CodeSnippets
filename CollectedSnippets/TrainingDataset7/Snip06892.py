def _from_sequence(self, seq):
        "Initialize the C OGR Envelope structure from the given sequence."
        self._envelope = OGREnvelope()
        self._envelope.MinX = seq[0]
        self._envelope.MinY = seq[1]
        self._envelope.MaxX = seq[2]
        self._envelope.MaxY = seq[3]