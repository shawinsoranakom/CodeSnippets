def test_dumpdata(self):
        "dumpdata honors allow_migrate restrictions on the router"
        User.objects.create_user("alice", "alice@example.com")
        User.objects.db_manager("default").create_user("bob", "bob@example.com")

        # dumping the default database doesn't try to include auth because
        # allow_migrate prohibits auth on default
        new_io = StringIO()
        management.call_command(
            "dumpdata", "auth", format="json", database="default", stdout=new_io
        )
        command_output = new_io.getvalue().strip()
        self.assertEqual(command_output, "[]")

        # dumping the other database does include auth
        new_io = StringIO()
        management.call_command(
            "dumpdata", "auth", format="json", database="other", stdout=new_io
        )
        command_output = new_io.getvalue().strip()
        self.assertIn('"email": "alice@example.com"', command_output)