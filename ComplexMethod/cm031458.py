def entry_ok(self):
        "Return entered module name as file path or None."
        name = self.entry.get().strip()
        if not name:
            self.showerror('no name specified.')
            return None
        # XXX Ought to insert current file's directory in front of path.
        try:
            spec = importlib.util.find_spec(name)
        except (ValueError, ImportError) as msg:
            self.showerror(str(msg))
            return None
        if spec is None:
            self.showerror("module not found.")
            return None
        if not isinstance(spec.loader, importlib.abc.SourceLoader):
            self.showerror("not a source-based module.")
            return None
        try:
            file_path = spec.loader.get_filename(name)
        except AttributeError:
            self.showerror("loader does not support get_filename.")
            return None
        except ImportError:
            # Some special modules require this (e.g. os.path)
            try:
                file_path = spec.loader.get_filename()
            except TypeError:
                self.showerror("loader failed to get filename.")
                return None
        return file_path