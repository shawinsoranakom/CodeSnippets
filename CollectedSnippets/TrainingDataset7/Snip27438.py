def test_run_python_invalid_reverse_code(self):
        msg = "RunPython must be supplied with callable arguments"
        with self.assertRaisesMessage(ValueError, msg):
            migrations.RunPython(code=migrations.RunPython.noop, reverse_code="invalid")