def eval_equation(self, s):

        if not TEST_ALL and random.random() < 0.90:
            return

        self.context.clear_flags()

        try:
            Sides = s.split('->')
            L = Sides[0].strip().split()
            id = L[0]
            if DEBUG:
                print("Test ", id, end=" ")
            funct = L[1].lower()
            valstemp = L[2:]
            L = Sides[1].strip().split()
            ans = L[0]
            exceptions = L[1:]
        except (TypeError, AttributeError, IndexError):
            raise self.decimal.InvalidOperation
        def FixQuotes(val):
            val = val.replace("''", 'SingleQuote').replace('""', 'DoubleQuote')
            val = val.replace("'", '').replace('"', '')
            val = val.replace('SingleQuote', "'").replace('DoubleQuote', '"')
            return val

        if id in self.skipped_test_ids:
            return

        fname = self.NameAdapter.get(funct, funct)
        if fname == 'rescale':
            return
        funct = getattr(self.context, fname)
        vals = []
        conglomerate = ''
        quote = 0
        theirexceptions = [self.ErrorNames[x.lower()] for x in exceptions]

        for exception in Signals[self.decimal]:
            self.context.traps[exception] = 1 #Catch these bugs...
        for exception in theirexceptions:
            self.context.traps[exception] = 0
        for i, val in enumerate(valstemp):
            if val.count("'") % 2 == 1:
                quote = 1 - quote
            if quote:
                conglomerate = conglomerate + ' ' + val
                continue
            else:
                val = conglomerate + val
                conglomerate = ''
            v = FixQuotes(val)
            if fname in ('to_sci_string', 'to_eng_string'):
                if EXTENDEDERRORTEST:
                    for error in theirexceptions:
                        self.context.traps[error] = 1
                        try:
                            funct(self.context.create_decimal(v))
                        except error:
                            pass
                        except Signals[self.decimal] as e:
                            self.fail("Raised %s in %s when %s disabled" % \
                                      (e, s, error))
                        else:
                            self.fail("Did not raise %s in %s" % (error, s))
                        self.context.traps[error] = 0
                v = self.context.create_decimal(v)
            else:
                v = self.read_unlimited(v, self.context)
            vals.append(v)

        ans = FixQuotes(ans)

        if EXTENDEDERRORTEST and fname not in ('to_sci_string', 'to_eng_string'):
            for error in theirexceptions:
                self.context.traps[error] = 1
                try:
                    funct(*vals)
                except error:
                    pass
                except Signals[self.decimal] as e:
                    self.fail("Raised %s in %s when %s disabled" % \
                              (e, s, error))
                else:
                    self.fail("Did not raise %s in %s" % (error, s))
                self.context.traps[error] = 0

            # as above, but add traps cumulatively, to check precedence
            ordered_errors = [e for e in OrderedSignals[self.decimal] if e in theirexceptions]
            for error in ordered_errors:
                self.context.traps[error] = 1
                try:
                    funct(*vals)
                except error:
                    pass
                except Signals[self.decimal] as e:
                    self.fail("Raised %s in %s; expected %s" %
                              (type(e), s, error))
                else:
                    self.fail("Did not raise %s in %s" % (error, s))
            # reset traps
            for error in ordered_errors:
                self.context.traps[error] = 0


        if DEBUG:
            print("--", self.context)
        try:
            result = str(funct(*vals))
            if fname in self.LogicalFunctions:
                result = str(int(eval(result))) # 'True', 'False' -> '1', '0'
        except Signals[self.decimal] as error:
            self.fail("Raised %s in %s" % (error, s))
        except: #Catch any error long enough to state the test case.
            print("ERROR:", s)
            raise

        myexceptions = self.getexceptions()

        myexceptions.sort(key=repr)
        theirexceptions.sort(key=repr)

        self.assertEqual(result, ans,
                         'Incorrect answer for ' + s + ' -- got ' + result)

        self.assertEqual(myexceptions, theirexceptions,
              'Incorrect flags set in ' + s + ' -- got ' + str(myexceptions))