def test_memory_stats_multigpu(self):
        # advance a generator with a end flag
        def advance(gen, end):
            if not end:
                try:
                    next(gen)
                except StopIteration:
                    end = True
            return end

        # interlace
        torch.cuda.empty_cache()
        gen0 = self._test_memory_stats_generator(self, device="cuda:0", N=35)
        gen1 = self._test_memory_stats_generator(
            self, device=torch.device("cuda:1"), N=35
        )
        end0 = end1 = False
        while not (end0 and end1):
            end0 = advance(gen0, end0)
            end1 = advance(gen1, end1)

        # semi-random order
        torch.cuda.empty_cache()
        gen0 = self._test_memory_stats_generator(self, device=0, N=35)
        gen1 = self._test_memory_stats_generator(
            self, device=torch.device("cuda:1"), N=35
        )
        end0 = end1 = False

        while not (end0 and end1):
            end0 = advance(gen0, end0)
            if not end0:
                gen1_max_times = torch.LongTensor(1).random_(0, 3)[0]
            else:
                gen1_max_times = torch.inf
            t = 0
            while t < gen1_max_times and not end1:
                end1 = advance(gen1, end1)
                t += 1