def gen():
            yield 1
            yield 2
            # Simulate that another thread is now rendering.
            # When the IfChangeNode stores state at 'self' it stays at '3' and
            # skip the last yielded value below.
            iter2 = iter([1, 2, 3])
            output2 = template.render(
                Context({"foo": range(3), "get_value": lambda: next(iter2)})
            )
            self.assertEqual(
                output2,
                "[0,1,2,3]",
                "Expected [0,1,2,3] in second parallel template, got {}".format(
                    output2
                ),
            )
            yield 3