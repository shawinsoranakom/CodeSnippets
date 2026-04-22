def on_moved(self, event: events.FileSystemEvent) -> None:
        self.handle_path_change_event(event)