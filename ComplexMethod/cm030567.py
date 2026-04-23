def check_track_dynamic(self, tp, always_track):
        x, y, z = 1.5, "a", []

        check = self._tracked if always_track else self._not_tracked
        check(tp())
        check(tp([]))
        check(tp(set()))
        check(tp([1, x, y]))
        check(tp(obj for obj in [1, x, y]))
        check(tp(set([1, x, y])))
        check(tp(tuple([obj]) for obj in [1, x, y]))
        check(tuple(tp([obj]) for obj in [1, x, y]))

        self._tracked(tp([z]))
        self._tracked(tp([[x, y]]))
        self._tracked(tp([{x: y}]))
        self._tracked(tp(obj for obj in [x, y, z]))
        self._tracked(tp(tuple([obj]) for obj in [x, y, z]))
        self._tracked(tuple(tp([obj]) for obj in [x, y, z]))

        t = tp([1, x, y, z])
        self.assertEqual(type(t), tp)
        self._tracked(t)
        self.assertEqual(type(t[:]), tuple)
        self._tracked(t[:])