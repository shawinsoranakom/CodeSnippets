def setUp(self):
        self.session = self.backend()
        # NB: be careful to delete any sessions created; stale sessions fill up
        # the /tmp (with some backends) and eventually overwhelm it after lots
        # of runs (think buildbots)
        self.addCleanup(self.session.delete)