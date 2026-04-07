def test_dumpdata_progressbar(self):
        """
        Dumpdata shows a progress bar on the command line when --output is set,
        stdout is a tty, and verbosity > 0.
        """
        management.call_command("loaddata", "fixture1.json", verbosity=0)
        new_io = StringIO()
        new_io.isatty = lambda: True
        with NamedTemporaryFile() as file:
            options = {
                "format": "json",
                "stdout": new_io,
                "stderr": new_io,
                "output": file.name,
            }
            management.call_command("dumpdata", "fixtures", **options)
            self.assertTrue(
                new_io.getvalue().endswith(
                    "[" + "." * ProgressBar.progress_width + "]\n"
                )
            )

            # Test no progress bar when verbosity = 0
            options["verbosity"] = 0
            new_io = StringIO()
            new_io.isatty = lambda: True
            options.update({"stdout": new_io, "stderr": new_io})
            management.call_command("dumpdata", "fixtures", **options)
            self.assertEqual(new_io.getvalue(), "")