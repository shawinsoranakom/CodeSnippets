def test_wrong_args(self):
        """
        Passing the wrong kinds of arguments outputs an error and prints usage.
        """
        out, err = self.run_django_admin(["startproject"])
        self.assertNoOutput(out)
        self.assertOutput(err, "usage:")
        self.assertOutput(err, "You must provide a project name.")