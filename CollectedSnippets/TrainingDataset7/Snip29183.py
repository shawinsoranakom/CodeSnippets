def test_pseudo_empty_fixtures(self):
        """
        A fixture can contain entries, but lead to nothing in the database;
        this shouldn't raise an error (#14068).
        """
        new_io = StringIO()
        management.call_command("loaddata", "pets", stdout=new_io, stderr=new_io)
        command_output = new_io.getvalue().strip()
        # No objects will actually be loaded
        self.assertEqual(
            command_output, "Installed 0 object(s) (of 2) from 1 fixture(s)"
        )