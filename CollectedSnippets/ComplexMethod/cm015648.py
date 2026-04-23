def test_default_logging(self, records):
        def fn(a):
            if a.sum() < 0:
                a = torch.sin(a)
            else:
                a = torch.cos(a)
            print("hello")
            return a + 1

        fn_opt = torch.compile(fn, backend="eager")
        fn_opt(torch.ones(10, 10))
        fn_opt(-torch.ones(10, 5))

        self.assertGreater(len([r for r in records if ".__graph_breaks" in r.name]), 0)
        self.assertGreater(len([r for r in records if ".__recompiles" in r.name]), 0)
        self.assertGreater(len([r for r in records if ".symbolic_shapes" in r.name]), 0)
        self.assertGreater(len([r for r in records if ".__guards" in r.name]), 0)
        self.assertGreater(
            len([r for r in records if "return a + 1" in r.getMessage()]), 0
        )