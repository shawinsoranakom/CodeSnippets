def check_branches(self, run_func, test_func=None, tool=TEST_TOOL, recorders=BRANCH_OFFSET_RECORDERS):
        if test_func is None:
            test_func = run_func
        try:
            self.assertEqual(sys.monitoring._all_events(), {})
            event_list = []
            all_events = 0
            for recorder in recorders:
                ev = recorder.event_type
                sys.monitoring.register_callback(tool, ev, recorder(event_list))
                all_events |= ev
            sys.monitoring.set_local_events(tool, test_func.__code__, all_events)
            run_func()
            sys.monitoring.set_local_events(tool, test_func.__code__, 0)
            for recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, None)
            lefts = set()
            rights = set()
            for (src, left, right) in test_func.__code__.co_branches():
                lefts.add((src, left))
                rights.add((src, right))
            for event in event_list:
                way, _, src, dest = event
                if "left" in way:
                    self.assertIn((src, dest), lefts)
                else:
                    self.assertIn("right", way)
                    self.assertIn((src, dest), rights)
        finally:
            sys.monitoring.set_local_events(tool, test_func.__code__, 0)
            for recorder in recorders:
                sys.monitoring.register_callback(tool, recorder.event_type, None)