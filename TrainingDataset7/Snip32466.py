def test_ordering_override(self):
        """
        Test if collectstatic takes files in proper order
        """
        self.assertFileContains("file2.txt", "duplicate of file2.txt")

        # run collectstatic again
        self.run_collectstatic()

        self.assertFileContains("file2.txt", "duplicate of file2.txt")