def main():
    constraints_path = 'test/lib/ansible_test/_data/requirements/constraints.txt'

    requirements = {}

    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        if path == 'test/lib/ansible_test/_data/requirements/ansible.txt':
            # This file is an exact copy of the ansible requirements.txt and should not conflict with other constraints.
            continue

        with open(path, 'r') as path_fd:
            requirements[path] = parse_requirements(path_fd.read().splitlines())

        if path == 'test/lib/ansible_test/_data/requirements/ansible-test.txt':
            # Special handling is required for ansible-test's requirements file.
            check_ansible_test(path, requirements.pop(path))
            continue

    frozen_sanity = {}
    non_sanity_requirements = set()

    for path, requirements in requirements.items():
        filename = os.path.basename(path)

        is_sanity = filename.startswith('sanity.') or filename.endswith('.requirements.txt')
        is_constraints = path == constraints_path

        for lineno, line, requirement in requirements:
            if not requirement:
                print('%s:%d:%d: cannot parse requirement: %s' % (path, lineno, 1, line))
                continue

            name = requirement.group('name').lower()
            raw_constraints = requirement.group('constraints')
            constraints = raw_constraints.strip()
            comment = requirement.group('comment')

            is_pinned = re.search('^ *== *[0-9.]+(rc[0-9]+)?(\\.post[0-9]+)?$', constraints)

            if is_sanity:
                sanity = frozen_sanity.setdefault(name, [])
                sanity.append((path, lineno, line, requirement))
            elif not is_constraints:
                non_sanity_requirements.add(name)

            if is_sanity:
                if not is_pinned:
                    # sanity test requirements must be pinned
                    print('%s:%d:%d: sanity test requirement (%s%s) must be frozen (use `==`)' % (path, lineno, 1, name, raw_constraints))

                continue

            if constraints and not is_constraints:
                allow_constraints = 'sanity_ok' in comment

                if not allow_constraints:
                    # keeping constraints for tests other than sanity tests in one file helps avoid conflicts
                    print('%s:%d:%d: put the constraint (%s%s) in `%s`' % (path, lineno, 1, name, raw_constraints, constraints_path))