def main():
    plugins = []
    for path in sys.argv[1:] or sys.stdin.read().splitlines():
        with open(path, 'rb') as f:
            try:
                mm_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            except ValueError:
                continue
            if DOC_RE.search(mm_file):
                plugins.append(path)
            mm_file.close()

    for plugin in plugins:
        data = {}
        data['doc'], data['examples'], data['return'], data['metadata'] = get_docstring(os.path.abspath(plugin), fragment_loader)
        for result in find_deprecations(data['doc']):
            print('%s: %s is scheduled for removal in %s' % (plugin, '.'.join(str(i) for i in result[0][:-2]), result[1]))

    base = os.path.join(os.path.dirname(ansible.config.__file__), 'base.yml')
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(ansible.__file__)))
    relative_base = os.path.relpath(base, root_path)

    with open(base) as f:
        data = yaml.safe_load(f)

    for result in find_deprecations(data):
        print('%s: %s is scheduled for removal in %s' % (relative_base, '.'.join(str(i) for i in result[0][:-2]), result[1]))