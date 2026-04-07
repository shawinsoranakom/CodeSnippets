def run_collectstatic(self, **kwargs):
        clear_filepath = os.path.join(settings.STATIC_ROOT, "cleared.txt")
        with open(clear_filepath, "w") as f:
            f.write("should be cleared")
        super().run_collectstatic(clear=True, **kwargs)