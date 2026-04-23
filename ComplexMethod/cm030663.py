def test_zippath_from_non_installed_posix(self):
        """
        Test that when create venv from non-installed python, the zip path
        value is as expected.
        """
        rmtree(self.env_dir)
        # First try to create a non-installed python. It's not a real full
        # functional non-installed python, but enough for this test.
        platlibdir = sys.platlibdir
        non_installed_dir = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(rmtree, non_installed_dir)
        bindir = os.path.join(non_installed_dir, self.bindir)
        os.mkdir(bindir)
        python_exe = os.path.basename(sys.executable)
        shutil.copy2(sys.executable, os.path.join(bindir, python_exe))
        libdir = os.path.join(non_installed_dir, platlibdir, self.lib[1])
        os.makedirs(libdir)
        landmark = os.path.join(libdir, "os.py")
        abi_thread = "t" if sysconfig.get_config_var("Py_GIL_DISABLED") else ""
        stdlib_zip = f"python{sys.version_info.major}{sys.version_info.minor}{abi_thread}"
        zip_landmark = os.path.join(non_installed_dir,
                                    platlibdir,
                                    stdlib_zip)
        additional_pythonpath_for_non_installed = []

        # Copy stdlib files to the non-installed python so venv can
        # correctly calculate the prefix.
        for eachpath in sys.path:
            if eachpath.endswith(".zip"):
                if os.path.isfile(eachpath):
                    shutil.copyfile(
                        eachpath,
                        os.path.join(non_installed_dir, platlibdir))
            elif os.path.isfile(os.path.join(eachpath, "os.py")):
                names = os.listdir(eachpath)
                ignored_names = copy_python_src_ignore(eachpath, names)
                for name in names:
                    if name in ignored_names:
                        continue
                    if name == "site-packages":
                        continue
                    fn = os.path.join(eachpath, name)
                    if os.path.isfile(fn):
                        shutil.copy(fn, libdir)
                    elif os.path.isdir(fn):
                        shutil.copytree(fn, os.path.join(libdir, name),
                                        ignore=copy_python_src_ignore)
            else:
                additional_pythonpath_for_non_installed.append(
                    eachpath)
        cmd = [os.path.join(non_installed_dir, self.bindir, python_exe),
               "-m",
               "venv",
               "--without-pip",
               "--without-scm-ignore-files",
               self.env_dir]
        # Our fake non-installed python is not fully functional because
        # it cannot find the extensions. Set PYTHONPATH so it can run the
        # venv module correctly.
        pythonpath = os.pathsep.join(
            additional_pythonpath_for_non_installed)
        # For python built with shared enabled. We need to set
        # LD_LIBRARY_PATH so the non-installed python can find and link
        # libpython.so
        ld_library_path = sysconfig.get_config_var("LIBDIR")
        if not ld_library_path or sysconfig.is_python_build():
            ld_library_path = os.path.abspath(os.path.dirname(sys.executable))
        if sys.platform == 'darwin':
            ld_library_path_env = "DYLD_LIBRARY_PATH"
        else:
            ld_library_path_env = "LD_LIBRARY_PATH"
        child_env = {
                "PYTHONPATH": pythonpath,
                ld_library_path_env: ld_library_path,
        }
        if asan_options := os.environ.get("ASAN_OPTIONS"):
            # prevent https://github.com/python/cpython/issues/104839
            child_env["ASAN_OPTIONS"] = asan_options
        subprocess.check_call(cmd, env=child_env)
        # Now check the venv created from the non-installed python has
        # correct zip path in pythonpath.
        target_python = os.path.join(self.env_dir, self.bindir, python_exe)
        cmd = [target_python, '-S', '-c', 'import sys; print(sys.path)']
        out, err = check_output(cmd)
        self.assertTrue(zip_landmark.encode() in out)