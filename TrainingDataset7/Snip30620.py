def test_ticket17429(self):
        """
        Meta.ordering=None works the same as Meta.ordering=[]
        """
        original_ordering = Tag._meta.ordering
        Tag._meta.ordering = None
        try:
            self.assertCountEqual(
                Tag.objects.all(),
                [self.t1, self.t2, self.t3, self.t4, self.t5],
            )
        finally:
            Tag._meta.ordering = original_ordering