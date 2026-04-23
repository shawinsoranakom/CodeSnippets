def test_c_signal_dict(self):

        # SignalDict coverage
        Context = C.Context
        DefaultContext = C.DefaultContext

        InvalidOperation = C.InvalidOperation
        FloatOperation = C.FloatOperation
        DivisionByZero = C.DivisionByZero
        Overflow = C.Overflow
        Subnormal = C.Subnormal
        Underflow = C.Underflow
        Rounded = C.Rounded
        Inexact = C.Inexact
        Clamped = C.Clamped

        DecClamped = C.DecClamped
        DecInvalidOperation = C.DecInvalidOperation
        DecIEEEInvalidOperation = C.DecIEEEInvalidOperation

        def assertIsExclusivelySet(signal, signal_dict):
            for sig in signal_dict:
                if sig == signal:
                    self.assertTrue(signal_dict[sig])
                else:
                    self.assertFalse(signal_dict[sig])

        c = DefaultContext.copy()

        # Signal dict methods
        self.assertTrue(Overflow in c.traps)
        c.clear_traps()
        for k in c.traps.keys():
            c.traps[k] = True
        for v in c.traps.values():
            self.assertTrue(v)
        c.clear_traps()
        for k, v in c.traps.items():
            self.assertFalse(v)

        self.assertFalse(c.flags.get(Overflow))
        self.assertIs(c.flags.get("x"), None)
        self.assertEqual(c.flags.get("x", "y"), "y")
        self.assertRaises(TypeError, c.flags.get, "x", "y", "z")

        self.assertEqual(len(c.flags), len(c.traps))
        s = sys.getsizeof(c.flags)
        s = sys.getsizeof(c.traps)
        s = c.flags.__repr__()

        # Set flags/traps.
        c.clear_flags()
        c._flags = DecClamped
        self.assertTrue(c.flags[Clamped])

        c.clear_traps()
        c._traps = DecInvalidOperation
        self.assertTrue(c.traps[InvalidOperation])

        # Set flags/traps from dictionary.
        c.clear_flags()
        d = c.flags.copy()
        d[DivisionByZero] = True
        c.flags = d
        assertIsExclusivelySet(DivisionByZero, c.flags)

        c.clear_traps()
        d = c.traps.copy()
        d[Underflow] = True
        c.traps = d
        assertIsExclusivelySet(Underflow, c.traps)

        # Random constructors
        IntSignals = {
          Clamped: C.DecClamped,
          Rounded: C.DecRounded,
          Inexact: C.DecInexact,
          Subnormal: C.DecSubnormal,
          Underflow: C.DecUnderflow,
          Overflow: C.DecOverflow,
          DivisionByZero: C.DecDivisionByZero,
          FloatOperation: C.DecFloatOperation,
          InvalidOperation: C.DecIEEEInvalidOperation
        }
        IntCond = [
          C.DecDivisionImpossible, C.DecDivisionUndefined, C.DecFpuError,
          C.DecInvalidContext, C.DecInvalidOperation, C.DecMallocError,
          C.DecConversionSyntax,
        ]

        lim = len(OrderedSignals[C])
        for r in range(lim):
            for t in range(lim):
                for round in RoundingModes:
                    flags = random.sample(OrderedSignals[C], r)
                    traps = random.sample(OrderedSignals[C], t)
                    prec = random.randrange(1, 10000)
                    emin = random.randrange(-10000, 0)
                    emax = random.randrange(0, 10000)
                    clamp = random.randrange(0, 2)
                    caps = random.randrange(0, 2)
                    cr = random.randrange(0, 2)
                    c = Context(prec=prec, rounding=round, Emin=emin, Emax=emax,
                                capitals=caps, clamp=clamp, flags=list(flags),
                                traps=list(traps))

                    self.assertEqual(c.prec, prec)
                    self.assertEqual(c.rounding, round)
                    self.assertEqual(c.Emin, emin)
                    self.assertEqual(c.Emax, emax)
                    self.assertEqual(c.capitals, caps)
                    self.assertEqual(c.clamp, clamp)

                    f = 0
                    for x in flags:
                        f |= IntSignals[x]
                    self.assertEqual(c._flags, f)

                    f = 0
                    for x in traps:
                        f |= IntSignals[x]
                    self.assertEqual(c._traps, f)

        for cond in IntCond:
            c._flags = cond
            self.assertTrue(c._flags&DecIEEEInvalidOperation)
            assertIsExclusivelySet(InvalidOperation, c.flags)

        for cond in IntCond:
            c._traps = cond
            self.assertTrue(c._traps&DecIEEEInvalidOperation)
            assertIsExclusivelySet(InvalidOperation, c.traps)