def test_hash_optional(self):
        from itertools import product

        if not RUN_ALL_HASH_TESTS:
            return

        # If specified, `expected` is a 2-tuple of expected
        # (number_of_collisions, pileup) values, and the test fails if
        # those aren't the values we get.  Also if specified, the test
        # fails if z > `zlimit`.
        def tryone_inner(tag, nbins, hashes, expected=None, zlimit=None):
            from collections import Counter

            nballs = len(hashes)
            mean, sdev = support.collision_stats(nbins, nballs)
            c = Counter(hashes)
            collisions = nballs - len(c)
            z = (collisions - mean) / sdev
            pileup = max(c.values()) - 1
            del c
            got = (collisions, pileup)
            failed = False
            prefix = ""
            if zlimit is not None and z > zlimit:
                failed = True
                prefix = f"FAIL z > {zlimit}; "
            if expected is not None and got != expected:
                failed = True
                prefix += f"FAIL {got} != {expected}; "
            if failed or JUST_SHOW_HASH_RESULTS:
                msg = f"{prefix}{tag}; pileup {pileup:,} mean {mean:.1f} "
                msg += f"coll {collisions:,} z {z:+.1f}"
                if JUST_SHOW_HASH_RESULTS:
                    import sys
                    print(msg, file=sys.__stdout__)
                else:
                    self.fail(msg)

        def tryone(tag, xs,
                   native32=None, native64=None, hi32=None, lo32=None,
                   zlimit=None):
            NHASHBITS = support.NHASHBITS
            hashes = list(map(hash, xs))
            tryone_inner(tag + f"; {NHASHBITS}-bit hash codes",
                         1 << NHASHBITS,
                         hashes,
                         native32 if NHASHBITS == 32 else native64,
                         zlimit)

            if NHASHBITS > 32:
                shift = NHASHBITS - 32
                tryone_inner(tag + "; 32-bit upper hash codes",
                             1 << 32,
                             [h >> shift for h in hashes],
                             hi32,
                             zlimit)

                mask = (1 << 32) - 1
                tryone_inner(tag + "; 32-bit lower hash codes",
                             1 << 32,
                             [h & mask for h in hashes],
                             lo32,
                             zlimit)

        # Tuples of smallish positive integers are common - nice if we
        # get "better than random" for these.
        tryone("range(100) by 3", list(product(range(100), repeat=3)),
               (0, 0), (0, 0), (4, 1), (0, 0))

        # A previous hash had systematic problems when mixing integers of
        # similar magnitude but opposite sign, obscurely related to that
        # j ^ -2 == -j when j is odd.
        cands = list(range(-10, -1)) + list(range(9))

        # Note:  -1 is omitted because hash(-1) == hash(-2) == -2, and
        # there's nothing the tuple hash can do to avoid collisions
        # inherited from collisions in the tuple components' hashes.
        tryone("-10 .. 8 by 4", list(product(cands, repeat=4)),
               (0, 0), (0, 0), (0, 0), (0, 0))
        del cands

        # The hashes here are a weird mix of values where all the
        # variation is in the lowest bits and across a single high-order
        # bit - the middle bits are all zeroes. A decent hash has to
        # both propagate low bits to the left and high bits to the
        # right.  This is also complicated a bit in that there are
        # collisions among the hashes of the integers in L alone.
        L = [n << 60 for n in range(100)]
        tryone("0..99 << 60 by 3", list(product(L, repeat=3)),
               (0, 0), (0, 0), (0, 0), (324, 1))
        del L

        # Used to suffer a massive number of collisions.
        tryone("[-3, 3] by 18", list(product([-3, 3], repeat=18)),
               (7, 1), (0, 0), (7, 1), (6, 1))

        # And even worse.  hash(0.5) has only a single bit set, at the
        # high end. A decent hash needs to propagate high bits right.
        tryone("[0, 0.5] by 18", list(product([0, 0.5], repeat=18)),
               (5, 1), (0, 0), (9, 1), (12, 1))

        # Hashes of ints and floats are the same across platforms.
        # String hashes vary even on a single platform across runs, due
        # to hash randomization for strings.  So we can't say exactly
        # what this should do.  Instead we insist that the # of
        # collisions is no more than 4 sdevs above the theoretically
        # random mean.  Even if the tuple hash can't achieve that on its
        # own, the string hash is trying to be decently pseudo-random
        # (in all bit positions) on _its_ own.  We can at least test
        # that the tuple hash doesn't systematically ruin that.
        tryone("4-char tuples",
               list(product("abcdefghijklmnopqrstuvwxyz", repeat=4)),
               zlimit=4.0)

        # The "old tuple test".  See https://bugs.python.org/issue942952.
        # Ensures, for example, that the hash:
        #   is non-commutative
        #   spreads closely spaced values
        #   doesn't exhibit cancellation in tuples like (x,(x,y))
        N = 50
        base = list(range(N))
        xp = list(product(base, repeat=2))
        inps = base + list(product(base, xp)) + \
                     list(product(xp, base)) + xp + list(zip(base))
        tryone("old tuple test", inps,
               (2, 1), (0, 0), (52, 49), (7, 1))
        del base, xp, inps

        # The "new tuple test".  See https://bugs.python.org/issue34751.
        # Even more tortured nesting, and a mix of signed ints of very
        # small magnitude.
        n = 5
        A = [x for x in range(-n, n+1) if x != -1]
        B = A + [(a,) for a in A]
        L2 = list(product(A, repeat=2))
        L3 = L2 + list(product(A, repeat=3))
        L4 = L3 + list(product(A, repeat=4))
        # T = list of testcases. These consist of all (possibly nested
        # at most 2 levels deep) tuples containing at most 4 items from
        # the set A.
        T = A
        T += [(a,) for a in B + L4]
        T += product(L3, B)
        T += product(L2, repeat=2)
        T += product(B, L3)
        T += product(B, B, L2)
        T += product(B, L2, B)
        T += product(L2, B, B)
        T += product(B, repeat=4)
        assert len(T) == 345130
        tryone("new tuple test", T,
               (9, 1), (0, 0), (21, 5), (6, 1))