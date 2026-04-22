def tearDown(self):
        fo = event_based_path_watcher._MultiPathWatcher.get_singleton()
        fo._observer.start.reset_mock()
        fo._observer.schedule.reset_mock()

        self.observer_class_patcher.stop()
        self.util_patcher.stop()