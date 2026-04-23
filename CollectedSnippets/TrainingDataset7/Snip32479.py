def test_no_remote_link(self):
        with self.assertRaisesMessage(
            CommandError, "Can't symlink to a remote destination."
        ):
            self.run_collectstatic()