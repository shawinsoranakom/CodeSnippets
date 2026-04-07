def post_process(self, *args, **kwargs):
        self.hashed_files = {}
        yield from super().post_process(*args, **kwargs)
        if not kwargs.get("dry_run"):
            self.save_manifest()