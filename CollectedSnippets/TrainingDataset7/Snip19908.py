def test_interactive_true_with_dependent_objects(self):
        """
        interactive mode (the default) deletes stale content types and warns of
        dependent objects.
        """
        post = Post.objects.create(title="post", content_type=self.content_type)
        # A related object is needed to show that a custom collector with
        # can_fast_delete=False is needed.
        ModelWithNullFKToSite.objects.create(post=post)
        with mock.patch("builtins.input", return_value="yes"):
            with captured_stdout() as stdout:
                call_command("remove_stale_contenttypes", verbosity=2, stdout=stdout)
        self.assertEqual(Post.objects.count(), 0)
        output = stdout.getvalue()
        self.assertIn("- Content type for contenttypes_tests.Fake", output)
        self.assertIn("- 1 contenttypes_tests.Post object(s)", output)
        self.assertIn("- 1 contenttypes_tests.ModelWithNullFKToSite", output)
        self.assertIn("Deleting stale content type", output)
        self.assertEqual(ContentType.objects.count(), self.before_count)