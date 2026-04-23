def close(self, *args, **kwargs) -> None:
        if self.closed:
            return
        if StreamWrapper.debug_unclosed_streams:
            del StreamWrapper.session_streams[self]
        if hasattr(self, "parent_stream") and self.parent_stream is not None:
            self.parent_stream.child_counter -= 1
            if (
                not self.parent_stream.child_counter
                and self.parent_stream.close_on_last_child
            ):
                self.parent_stream.close()
        try:
            self.file_obj.close(*args, **kwargs)
        except AttributeError:
            pass
        self.closed = True