def setUp(self):
        # This test suite patches MultiPathWatcher. A MultiPathWatcher may
        # already exist (another test may have directly or indirectly created
        # one), so we first close any existing watcher instance here.
        if event_based_path_watcher._MultiPathWatcher._singleton is not None:
            event_based_path_watcher._MultiPathWatcher.get_singleton().close()
            event_based_path_watcher._MultiPathWatcher._singleton = None

        self.observer_class_patcher = mock.patch(
            "streamlit.watcher.event_based_path_watcher.Observer"
        )
        self.util_patcher = mock.patch(
            "streamlit.watcher.event_based_path_watcher.util"
        )
        self.MockObserverClass = self.observer_class_patcher.start()
        self.mock_util = self.util_patcher.start()