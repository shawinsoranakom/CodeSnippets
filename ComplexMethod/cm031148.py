def setup_python(self, context):
            """
            Set up a Python executable in the environment.

            :param context: The information for the environment creation request
                            being processed.
            """
            binpath = context.bin_path
            dirname = context.python_dir
            exename = os.path.basename(context.env_exe)
            exe_stem = os.path.splitext(exename)[0]
            exe_d = '_d' if os.path.normcase(exe_stem).endswith('_d') else ''
            if sysconfig.is_python_build():
                scripts = dirname
            else:
                scripts = os.path.join(os.path.dirname(__file__),
                                       'scripts', 'nt')
            if not sysconfig.get_config_var("Py_GIL_DISABLED"):
                python_exe = os.path.join(dirname, f'python{exe_d}.exe')
                pythonw_exe = os.path.join(dirname, f'pythonw{exe_d}.exe')
                link_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                }
                python_exe = os.path.join(scripts, f'venvlauncher{exe_d}.exe')
                pythonw_exe = os.path.join(scripts, f'venvwlauncher{exe_d}.exe')
                copy_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                }
            else:
                exe_t = f'3.{sys.version_info[1]}t'
                python_exe = os.path.join(dirname, f'python{exe_t}{exe_d}.exe')
                pythonw_exe = os.path.join(dirname, f'pythonw{exe_t}{exe_d}.exe')
                link_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    f'python{exe_t}.exe': python_exe,
                    f'python{exe_t}{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                    f'pythonw{exe_t}.exe': pythonw_exe,
                    f'pythonw{exe_t}{exe_d}.exe': pythonw_exe,
                }
                python_exe = os.path.join(scripts, f'venvlaunchert{exe_d}.exe')
                pythonw_exe = os.path.join(scripts, f'venvwlaunchert{exe_d}.exe')
                copy_sources = {
                    'python.exe': python_exe,
                    f'python{exe_d}.exe': python_exe,
                    f'python{exe_t}.exe': python_exe,
                    f'python{exe_t}{exe_d}.exe': python_exe,
                    'pythonw.exe': pythonw_exe,
                    f'pythonw{exe_d}.exe': pythonw_exe,
                    f'pythonw{exe_t}.exe': pythonw_exe,
                    f'pythonw{exe_t}{exe_d}.exe': pythonw_exe,
                }

            do_copies = True
            if self.symlinks:
                do_copies = False
                # For symlinking, we need all the DLLs to be available alongside
                # the executables.
                link_sources.update({
                    f: os.path.join(dirname, f) for f in os.listdir(dirname)
                    if os.path.normcase(f).startswith(('python', 'vcruntime'))
                    and os.path.normcase(os.path.splitext(f)[1]) == '.dll'
                })

                to_unlink = []
                for dest, src in link_sources.items():
                    dest = os.path.join(binpath, dest)
                    try:
                        os.symlink(src, dest)
                        to_unlink.append(dest)
                    except OSError:
                        logger.warning('Unable to symlink %r to %r', src, dest)
                        do_copies = True
                        for f in to_unlink:
                            try:
                                os.unlink(f)
                            except OSError:
                                logger.warning('Failed to clean up symlink %r',
                                               f)
                        logger.warning('Retrying with copies')
                        break

            if do_copies:
                for dest, src in copy_sources.items():
                    dest = os.path.join(binpath, dest)
                    try:
                        shutil.copy2(src, dest)
                    except OSError:
                        logger.warning('Unable to copy %r to %r', src, dest)

            if sysconfig.is_python_build():
                # copy init.tcl
                for root, dirs, files in os.walk(context.python_dir):
                    if 'init.tcl' in files:
                        tcldir = os.path.basename(root)
                        tcldir = os.path.join(context.env_dir, 'Lib', tcldir)
                        if not os.path.exists(tcldir):
                            os.makedirs(tcldir)
                        src = os.path.join(root, 'init.tcl')
                        dst = os.path.join(tcldir, 'init.tcl')
                        shutil.copyfile(src, dst)
                        break