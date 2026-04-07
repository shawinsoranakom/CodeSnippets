def test_multiple_forwards_only_m2m(self):
        # Regression for #24505 - Multiple ManyToManyFields to same "to"
        # model with related_name set to '+'.
        foo = Line.objects.create(name="foo")
        bar = Line.objects.create(name="bar")
        post = Post.objects.create()
        post.primary_lines.add(foo)
        post.secondary_lines.add(bar)
        self.assertSequenceEqual(post.primary_lines.all(), [foo])
        self.assertSequenceEqual(post.secondary_lines.all(), [bar])