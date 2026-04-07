def _collectstatic_output(self, verbosity=3, **kwargs):
        """
        Run collectstatic, and capture and return the output.
        """
        out = StringIO()
        call_command(
            "collectstatic",
            interactive=False,
            verbosity=verbosity,
            stdout=out,
            **kwargs,
        )
        return out.getvalue()