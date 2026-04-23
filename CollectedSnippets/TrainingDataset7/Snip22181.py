def test_loaddata_verbosity_three(self):
        output = StringIO()
        management.call_command(
            "loaddata", "fixture1.json", verbosity=3, stdout=output, stderr=output
        )
        command_output = output.getvalue()
        self.assertIn(
            "\rProcessed 1 object(s).\rProcessed 2 object(s)."
            "\rProcessed 3 object(s).\rProcessed 4 object(s).\n",
            command_output,
        )