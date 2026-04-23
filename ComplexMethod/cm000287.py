def _choose_a1(self):
        """
        Choose first alpha
        Steps:
            1: First loop over all samples
            2: Second loop over all non-bound samples until no non-bound samples violate
               the KKT condition.
            3: Repeat these two processes until no samples violate the KKT condition
               after the first loop.
        """
        while True:
            all_not_obey = True
            # all sample
            print("Scanning all samples!")
            for i1 in [i for i in self._all_samples if self._check_obey_kkt(i)]:
                all_not_obey = False
                yield from self._choose_a2(i1)

            # non-bound sample
            print("Scanning non-bound samples!")
            while True:
                not_obey = True
                for i1 in [
                    i
                    for i in self._all_samples
                    if self._check_obey_kkt(i) and self._is_unbound(i)
                ]:
                    not_obey = False
                    yield from self._choose_a2(i1)
                if not_obey:
                    print("All non-bound samples satisfy the KKT condition!")
                    break
            if all_not_obey:
                print("All samples satisfy the KKT condition!")
                break
        return False