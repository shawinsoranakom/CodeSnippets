def save(self):
        for filename, sources in list(self.files.items()):
            if sources:
                d, fn = os.path.split(filename)
                try:
                    os.makedirs(d)
                except OSError as ex:
                    if not os.path.isdir(d):
                        self.module.fail_json("Failed to create directory %s: %s" % (d, to_native(ex)))

                try:
                    fd, tmp_path = tempfile.mkstemp(prefix=".%s-" % fn, dir=d)
                except OSError as ex:
                    raise Exception(f'Unable to create temp file at {d!r} for apt source.') from ex

                f = os.fdopen(fd, 'w')
                for n, valid, enabled, source, comment in sources:
                    chunks = []
                    if not enabled:
                        chunks.append('# ')
                    chunks.append(source)
                    if comment:
                        chunks.append(' # ')
                        chunks.append(comment)
                    chunks.append('\n')
                    line = ''.join(chunks)

                    try:
                        f.write(line)
                    except OSError as ex:
                        raise Exception(f"Failed to write to file {tmp_path!r}.") from ex
                if filename in self.files_mapping:
                    # Write to symlink target instead of replacing symlink as a normal file
                    self.module.atomic_move(tmp_path, self.files_mapping[filename])
                else:
                    self.module.atomic_move(tmp_path, filename)

                # allow the user to override the default mode
                if filename in self.new_repos:
                    this_mode = self.module.params.get('mode', DEFAULT_SOURCES_PERM)
                    self.module.set_mode_if_different(filename, this_mode, False)
            else:
                del self.files[filename]
                if os.path.exists(filename):
                    os.remove(filename)