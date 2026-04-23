def run_collectstatic(self, *, verbosity=0, **kwargs):
        call_command(
            "collectstatic",
            interactive=False,
            verbosity=verbosity,
            ignore_patterns=["*.ignoreme"],
            **kwargs,
        )