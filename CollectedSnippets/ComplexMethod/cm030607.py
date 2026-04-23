def iter_action_sets(self):
        # - used / not used  (associated / not associated)
        # - empty / emptied / never emptied / partly emptied
        # - closed / not closed
        # - released / not released

        # never used
        yield []

        # only pre-closed (and possible used after)
        for closeactions in self._iter_close_action_sets('same', 'other'):
            yield closeactions
            for postactions in self._iter_post_close_action_sets():
                yield closeactions + postactions
        for closeactions in self._iter_close_action_sets('other', 'extra'):
            yield closeactions
            for postactions in self._iter_post_close_action_sets():
                yield closeactions + postactions

        # used
        for useactions in self._iter_use_action_sets('same', 'other'):
            yield useactions
            for closeactions in self._iter_close_action_sets('same', 'other'):
                actions = useactions + closeactions
                yield actions
                for postactions in self._iter_post_close_action_sets():
                    yield actions + postactions
            for closeactions in self._iter_close_action_sets('other', 'extra'):
                actions = useactions + closeactions
                yield actions
                for postactions in self._iter_post_close_action_sets():
                    yield actions + postactions
        for useactions in self._iter_use_action_sets('other', 'extra'):
            yield useactions
            for closeactions in self._iter_close_action_sets('same', 'other'):
                actions = useactions + closeactions
                yield actions
                for postactions in self._iter_post_close_action_sets():
                    yield actions + postactions
            for closeactions in self._iter_close_action_sets('other', 'extra'):
                actions = useactions + closeactions
                yield actions
                for postactions in self._iter_post_close_action_sets():
                    yield actions + postactions