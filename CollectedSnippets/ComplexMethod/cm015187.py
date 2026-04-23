def tearDown(self):
        interesting = []
        for o in gc.get_objects():
            if (
                isinstance(o, (torch.Tensor, Dim, Tensor, DimList))
                and id(o) not in self.interesting
            ):
                interesting.append(o)

        extra_memory = 0
        if "cuda" in self._testMethodName:
            extra_memory += torch.cuda.memory_allocated() - self.mem_allocated

        #  nolevels = _n_levels_in_use() == 0
        if extra_memory != 0 or len(interesting) != 0:
            import refcycle

            refcycle.garbage().export_image("garbage.pdf")
        gc.collect()
        # assert nolevels, f"cleanup failed? {_n_levels_in_use()}"
        self.assertEqual(
            extra_memory, 0, f"extra cuda memory left allocated: {extra_memory}"
        )
        self.assertEqual(
            len(interesting),
            0,
            (
                f"extra torch.Tensor, Dim, or Tensor left allocated: {len(interesting)} objects of types:"
                f"{[type(t) for t in interesting]}"
            ),
        )