def run(self):
        _logger.info('AutoReload watcher running with inotify')
        dir_creation_events = set(('IN_MOVED_TO', 'IN_CREATE'))
        while self.started:
            for event in self.watcher.event_gen(timeout_s=0, yield_nones=False):
                (_, type_names, path, filename) = event
                if 'IN_ISDIR' not in type_names:
                    # despite not having IN_DELETE in the watcher's mask, the
                    # watcher sends these events when a directory is deleted.
                    if 'IN_DELETE' not in type_names:
                        full_path = os.path.join(path, filename)
                        if self.handle_file(full_path):
                            return
                elif dir_creation_events.intersection(type_names):
                    full_path = os.path.join(path, filename)
                    for root, _, files in os.walk(full_path):
                        for file in files:
                            if self.handle_file(os.path.join(root, file)):
                                return