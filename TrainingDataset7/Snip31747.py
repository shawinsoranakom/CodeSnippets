def test_dumpdata_pyyaml_error_message(self):
        """Calling dumpdata produces an error when yaml package missing"""
        with self.assertRaisesMessage(
            management.CommandError, YAML_IMPORT_ERROR_MESSAGE
        ):
            management.call_command("dumpdata", format="yaml")