def initialize_suite(self):
        if multiprocessing.get_start_method() in {"forkserver", "spawn"}:
            self.initial_settings = {
                alias: connections[alias].settings_dict for alias in connections
            }
            self.serialized_contents = {
                alias: connections[alias]._test_serialized_contents
                for alias in connections
                if alias in self.serialized_aliases
            }