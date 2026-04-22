def on_created(self, event: events.FileSystemEvent) -> None:
        self.handle_path_change_event(event)