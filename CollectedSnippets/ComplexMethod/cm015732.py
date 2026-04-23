def testStressfully(self):
        # Try a variety of sizes at and around powers of 2, and at powers of 10.
        sizes = [0]
        for power in range(1, 10):
            n = 2 ** power
            sizes.extend(range(n-1, n+2))
        sizes.extend([10, 100, 1000])

        with torch._dynamo.error_on_graph_break(False):
            class Complains(object):
                maybe_complain = True

                def __init__(self, i):
                    self.i = i

                def __lt__(self, other):
                    if Complains.maybe_complain and random.random() < 0.001:
                        if verbose:
                            print("        complaining at", self, other)
                        raise RuntimeError
                    return self.i < other.i

                def __repr__(self):
                    return "Complains(%d)" % self.i

            class Stable(object):
                def __init__(self, key, i):
                    self.key = key
                    self.index = i

                def __lt__(self, other):
                    return self.key < other.key

                def __repr__(self):
                    return "Stable(%d, %d)" % (self.key, self.index)

        for n in sizes:
            x = list(range(n))
            if verbose:
                print("Testing size", n)

            s = x[:]
            check("identity", x, s)

            s = x[:]
            s.reverse()
            check("reversed", x, s)

            s = x[:]
            random.shuffle(s)
            check("random permutation", x, s)

            y = x[:]
            y.reverse()
            s = x[:]
            check("reversed via function", y, s, lambda a, b: (b>a)-(b<a))

            if verbose:
                print("    Checking against an insane comparison function.")
                print("        If the implementation isn't careful, this may segfault.")
            s = x[:]
            s.sort(key=cmp_to_key(lambda a, b:  int(random.random() * 3) - 1))
            check("an insane function left some permutation", x, s)

            if len(x) >= 2:
                def bad_key(x):
                    raise RuntimeError
                s = x[:]
                self.assertRaises(RuntimeError, s.sort, key=bad_key)

            x = [Complains(i) for i in x]
            s = x[:]
            random.shuffle(s)
            Complains.maybe_complain = True
            it_complained = False
            try:
                s.sort()
            except RuntimeError:
                it_complained = True
            if it_complained:
                Complains.maybe_complain = False
                check("exception during sort left some permutation", x, s)

            s = [Stable(random.randrange(10), i) for i in range(n)]
            augmented = [(e, e.index) for e in s]
            augmented.sort()    # forced stable because ties broken by index
            x = [e for e, i in augmented] # a stable sort of s
            check("stability", x, s)