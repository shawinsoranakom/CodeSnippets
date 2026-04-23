def count_path(self, path, exclude=None):
        path = path.rstrip('/')
        exclude_list = []
        for i in odoo.modules.module.MANIFEST_NAMES:
            manifest_path = os.path.join(path, i)
            try:
                with open(manifest_path, 'rb') as manifest:
                    exclude_list.extend(DEFAULT_EXCLUDE)
                    d = ast.literal_eval(manifest.read().decode('latin1'))
                    for j in ['cloc_exclude', 'demo', 'demo_xml']:
                        exclude_list.extend(d.get(j, []))
                    break
            except Exception:
                pass
        if not exclude:
            exclude = set()
        for i in filter(None, exclude_list):
            exclude.update(str(p) for p in pathlib.Path(path).glob(i))

        module_name = os.path.basename(path)
        self.book(module_name)
        for root, _dirs, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                if file_path in exclude:
                    continue

                ext = os.path.splitext(file_path)[1].lower()
                if ext not in VALID_EXTENSION:
                    continue

                if os.path.getsize(file_path) > MAX_FILE_SIZE:
                    self.book(module_name, file_path, (-1, "Max file size exceeded"))
                    continue

                with open(file_path, 'rb') as f:
                    # Decode using latin1 to avoid error that may raise by decoding with utf8
                    # The chars not correctly decoded in latin1 have no impact on how many lines will be counted
                    content = f.read().decode('latin1')
                self.book(module_name, file_path, self.parse(content, ext))