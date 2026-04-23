def run_ops(
        self,
        name,
        ops,
        ctor_order=None,
        dtor_order=None,
        results=None,
        expect_raises=False,
    ):
        """
        Given a list of operator registrations, run the registrations in the
        order specified by ctor_order, and then run the deregistrations in
        dtor_order.

        If results is specified, intermediate results are checked for consistency
        with results stored in results (and stored in results if this is the
        first time we've seen them).  Results are expected to be equivalent
        modulo commutativity and inverses (thus, results is keyed on a frozenset
        of in effect registrations from ops).  Results stores namedtuple
        Result[state, table, provenance], where state is a string that contains
        non-derived kernel registered or error message if it doesn't pass;
        table is a string that contains computed dispatch table entries;
        provenance is a string that describes how exactly we got this string.

        If expect_raises is True, it is not an error to raise an exception.  Instead,
        we'll store the exception string (instead of the dispatcher state)
        in results.  In principle we should flag these differently, but it's
        very obvious when you get an error in one case but not another.
        """
        # By allocating every test into a fresh namespace, this makes it less
        # likely that a bug in the testing framework will result in tests
        # interfering with each other
        self.__class__.namespace_index += 1
        if results is None:
            results = {}
        if ctor_order is None:
            ctor_order = list(range(len(ops)))
        if dtor_order is None:
            dtor_order = list(reversed(ctor_order))
        # Refs which retain the c10::Module object so we can explicitly control
        # when each deregistration happens (deregistration occurs when the
        # object gets deallocated).
        refs = [None] * len(ops)
        # Keep track of the set "in effect" registrations
        active_ops = set()

        # double underscore to make it less likely we conflict with something
        # else
        test_namespace = f"__test{self.namespace_index}__"

        def check_invariants(actual_provenance):
            C._dispatch_check_invariants(name)
            # Normalize the test namespace so that expected outputs are stable
            actual_state = C._dispatch_dump(f"{test_namespace}::{name}").replace(
                test_namespace, "test"
            )
            actual_table = C._dispatch_dump_table(f"{test_namespace}::{name}").replace(
                test_namespace, "test"
            )
            expected_state, expected_table, expected_provenance = results.setdefault(
                frozenset(active_ops),
                Result(actual_state, actual_table, actual_provenance),
            )
            self.assertMultiLineEqual(
                expected_state,
                actual_state,
                f"expected from {expected_provenance}; actual from {actual_provenance}",
            )
            self.assertMultiLineEqual(
                expected_table,
                actual_table,
                f"expected from {expected_provenance}; actual from {actual_provenance}",
            )

        results.setdefault(frozenset(), Result("", "", "hardcoded initial state"))
        check_invariants("initial state")
        # In the order specified by ctor_order, run registrations
        set_to_report = frozenset(range(len(ops)))
        for i, op_ix in enumerate(ctor_order):
            # It would be better to DEF here, but because we manage
            # lifetime of multiple registrations with multiple Library
            # references (refs), we can't deal with the strict checking
            # from DEF.
            refs[op_ix] = C._dispatch_library("FRAGMENT", test_namespace, "")
            active_ops.add(op_ix)
            try:
                ops[op_ix](refs[op_ix])
                check_invariants(f"running ctors {ctor_order[: i + 1]}")
            except RuntimeError as e:
                if not expect_raises:
                    raise
                actual = str(e).replace(test_namespace, "test")
                actual = actual.split("\nException raised from ")[0]
                expected, _, expected_provenance = results.setdefault(
                    frozenset(active_ops),
                    Result(
                        actual, "", f"error after running ctors {ctor_order[: i + 1]}"
                    ),
                )
                self.assertMultiLineEqual(expected, actual, expected_provenance)
                set_to_report = frozenset(active_ops)
                active_ops.remove(op_ix)
                # NB: this finally test asserts that if a registrations fails,
                # the dispatcher is left in the same state *that it was before*!
                check_invariants(
                    f"running ctors {ctor_order[:i]} and then failing to run ctor {op_ix} "
                    "(did this failure leave the dispatcher in a wedged state? "
                    "it shouldn't!)"
                )
                break
        last_ctor = i
        if expect_raises and len(active_ops) == len(ops):
            # Destroy references first, as some test frameworks (like pytest)
            # will retain references in the exception raised by assertTrue! EW!
            refs = None
            self.assertTrue(
                False,
                "expected exception to be raised, but nothing was raised "
                f"(after running ctors {ctor_order})",
            )
        # In the order specified by dtor_order, run deregistrations
        for i, op_ix in enumerate(dtor_order):
            # Trigger a destruction
            refs[op_ix] = None
            # discard not remove, since we may not have actually deregistered
            # anything if there was an error raised
            if expect_raises:
                active_ops.discard(op_ix)
            else:
                active_ops.remove(op_ix)
            check_invariants(
                f"running ctors {ctor_order[: last_ctor + 1]}, then running dtors {dtor_order[: i + 1]}"
            )
        return results[set_to_report][0]