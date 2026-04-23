def __init__(self, path: str, module_utils: set[str]) -> None:
        self.path = path
        self.module_utils = module_utils
        self.imports: set[str] = set()

        # implicitly import parent package

        if path.endswith('/__init__.py'):
            path = os.path.split(path)[0]

        if path.startswith('lib/ansible/module_utils/'):
            package = os.path.split(path)[0].replace('/', '.')[4:]

            if package != 'ansible.module_utils' and package not in VIRTUAL_PACKAGES:
                self.add_import(package, 0)

        self.module = None

        if data_context().content.is_ansible:
            # Various parts of the Ansible source tree execute within different modules.
            # To support import analysis, each file which uses relative imports must reside under a path defined here.
            # The mapping is a tuple consisting of a path pattern to match and a replacement path.
            # During analysis, any relative imports not covered here will result in warnings, which can be fixed by adding the appropriate entry.
            path_map = (
                ('^lib/ansible/', 'ansible/'),
                ('^test/lib/ansible_test/_util/controller/sanity/validate-modules/', 'validate_modules/'),
                ('^test/units/', 'test/units/'),
                ('^test/lib/ansible_test/_internal/', 'ansible_test/_internal/'),
                ('^test/integration/targets/.*/ansible_collections/(?P<ns>[^/]*)/(?P<col>[^/]*)/', r'ansible_collections/\g<ns>/\g<col>/'),
                ('^test/integration/targets/.*/library/', 'ansible/modules/'),
            )

            for pattern, replacement in path_map:
                if re.search(pattern, self.path):
                    revised_path = re.sub(pattern, replacement, self.path)
                    self.module = path_to_module(revised_path)
                    break
        else:
            # This assumes that all files within the collection are executed by Ansible as part of the collection.
            # While that will usually be true, there are exceptions which will result in this resolution being incorrect.
            self.module = path_to_module(os.path.join(data_context().content.collection.directory, self.path))