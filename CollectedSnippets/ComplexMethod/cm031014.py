def find_tests(self, tests: TestList | None = None) -> tuple[TestTuple, TestList | None]:
        if tests is None:
            tests = []
        if self.single_test_run:
            self.next_single_filename = os.path.join(self.tmp_dir, 'pynexttest')
            try:
                with open(self.next_single_filename, 'r') as fp:
                    next_test = fp.read().strip()
                    tests = [next_test]
            except OSError:
                pass

        if self.fromfile:
            tests = []
            # regex to match 'test_builtin' in line:
            # '0:00:00 [  4/400] test_builtin -- test_dict took 1 sec'
            regex = re.compile(r'\btest_[a-zA-Z0-9_]+\b')
            with open(os.path.join(os_helper.SAVEDCWD, self.fromfile)) as fp:
                for line in fp:
                    line = line.split('#', 1)[0]
                    line = line.strip()
                    match = regex.search(line)
                    if match is not None:
                        tests.append(match.group())

        strip_py_suffix(tests)

        exclude_tests = set()
        if self.exclude:
            for arg in self.cmdline_args:
                exclude_tests.add(arg)
            self.cmdline_args = []

        if self.pgo:
            # add default PGO tests if no tests are specified
            setup_pgo_tests(self.cmdline_args, self.pgo_extended)

        if self.tsan:
            setup_tsan_tests(self.cmdline_args)

        if self.tsan_parallel:
            setup_tsan_parallel_tests(self.cmdline_args)

        alltests = findtests(testdir=self.test_dir,
                             exclude=exclude_tests)

        if not self.fromfile:
            selected = tests or self.cmdline_args
            if exclude_tests:
                # Support "--pgo/--tsan -x test_xxx" command
                selected = [name for name in selected
                            if name not in exclude_tests]
            if selected:
                selected = split_test_packages(selected)
            else:
                selected = alltests
        else:
            selected = tests

        if self.single_test_run:
            selected = selected[:1]
            try:
                pos = alltests.index(selected[0])
                self.next_single_test = alltests[pos + 1]
            except IndexError:
                pass

        # Remove all the selected tests that precede start if it's set.
        if self.starting_test:
            try:
                del selected[:selected.index(self.starting_test)]
            except ValueError:
                print(f"Cannot find starting test: {self.starting_test}")
                sys.exit(1)

        random.seed(self.random_seed)
        if self.randomize:
            random.shuffle(selected)

        for priority_test in reversed(self.prioritize_tests):
            try:
                selected.remove(priority_test)
            except ValueError:
                print(f"warning: --prioritize={priority_test} used"
                        f" but test not actually selected")
                continue
            else:
                selected.insert(0, priority_test)

        return (tuple(selected), tests)