def on_modified(self, event: events.FileSystemEvent) -> None:
        self.handle_path_change_event(event)