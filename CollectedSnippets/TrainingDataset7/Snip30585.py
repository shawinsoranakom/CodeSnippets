def test_avoid_infinite_loop_on_too_many_subqueries(self):
        x = Tag.objects.filter(pk=1)
        local_recursion_limit = sys.getrecursionlimit() // 16
        msg = "Maximum recursion depth exceeded: too many subqueries."
        with self.assertRaisesMessage(RecursionError, msg):
            for i in range(local_recursion_limit + 2):
                x = Tag.objects.filter(pk__in=x)