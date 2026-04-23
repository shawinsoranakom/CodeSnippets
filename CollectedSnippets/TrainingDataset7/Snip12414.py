def _flag_dead_receivers(self, reference=None):
        # Mark that the self.receivers list has dead weakrefs. If so, we will
        # clean those up in connect, disconnect and _live_receivers while
        # holding self.lock. Note that doing the cleanup here isn't a good
        # idea, _flag_dead_receivers() will be called as side effect of garbage
        # collection, and so the call can happen while we are already holding
        # self.lock.
        self._dead_receivers = True