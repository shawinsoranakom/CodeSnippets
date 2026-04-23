def install_scripts(self, context, path):
        """
        Install scripts into the created environment from a directory.

        :param context: The information for the environment creation request
                        being processed.
        :param path:    Absolute pathname of a directory containing script.
                        Scripts in the 'common' subdirectory of this directory,
                        and those in the directory named for the platform
                        being run on, are installed in the created environment.
                        Placeholder variables are replaced with environment-
                        specific values.
        """
        binpath = context.bin_path
        plen = len(path)
        if os.name == 'nt':
            def skip_file(f):
                f = os.path.normcase(f)
                return (f.startswith(('python', 'venv'))
                        and f.endswith(('.exe', '.pdb')))
        else:
            def skip_file(f):
                return False
        for root, dirs, files in os.walk(path):
            if root == path:  # at top-level, remove irrelevant dirs
                for d in dirs[:]:
                    if d not in ('common', os.name):
                        dirs.remove(d)
                continue  # ignore files in top level
            for f in files:
                if skip_file(f):
                    continue
                srcfile = os.path.join(root, f)
                suffix = root[plen:].split(os.sep)[2:]
                if not suffix:
                    dstdir = binpath
                else:
                    dstdir = os.path.join(binpath, *suffix)
                if not os.path.exists(dstdir):
                    os.makedirs(dstdir)
                dstfile = os.path.join(dstdir, f)
                if os.name == 'nt' and srcfile.endswith(('.exe', '.pdb')):
                    shutil.copy2(srcfile, dstfile)
                    continue
                with open(srcfile, 'rb') as f:
                    data = f.read()
                try:
                    context.script_path = srcfile
                    new_data = (
                        self.replace_variables(data.decode('utf-8'), context)
                            .encode('utf-8')
                    )
                except UnicodeError as e:
                    logger.warning('unable to copy script %r, '
                                   'may be binary: %s', srcfile, e)
                    continue
                if new_data == data:
                    shutil.copy(srcfile, dstfile)
                else:
                    with open(dstfile, 'wb') as f:
                        f.write(new_data)
                    shutil.copymode(srcfile, dstfile)