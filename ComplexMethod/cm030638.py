def check_resurrecting_chain(self, classes):
        N = len(classes)
        def dummy_callback(ref):
            pass
        with SimpleBase.test():
            nodes = self.build_chain(classes)
            N = len(nodes)
            ids = [id(s) for s in nodes]
            survivor_ids = [id(s) for s in nodes if isinstance(s, SimpleResurrector)]
            wrs = [weakref.ref(s) for s in nodes]
            wrcs = [weakref.ref(s, dummy_callback) for s in nodes]
            del nodes
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors(survivor_ids)
            for wr in wrs:
                # These values used to be None because weakrefs were cleared
                # before calling finalizers.  Now they are cleared after.
                self.assertIsNotNone(wr())
            for wr in wrcs:
                # Weakrefs with callbacks are still cleared before calling
                # finalizers.
                self.assertIsNone(wr())
            self.clear_survivors()
            gc.collect()
            self.assert_del_calls(ids)
            self.assert_survivors([])