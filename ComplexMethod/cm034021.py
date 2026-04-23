def tmpdir(self):
        # if _ansible_tmpdir was not set and we have a remote_tmp,
        # the module needs to create it and clean it up once finished.
        # otherwise we create our own module tmp dir from the system defaults
        if self._tmpdir is None:
            basedir = None

            if self._remote_tmp is not None:
                basedir = os.path.expanduser(os.path.expandvars(self._remote_tmp))

            if basedir is not None and not os.path.exists(basedir):
                try:
                    os.makedirs(basedir, mode=0o700)
                except OSError as ex:
                    self.error_as_warning(
                        msg=f"Unable to use {basedir!r} as temporary directory, falling back to system default.",
                        exception=ex,
                    )
                    basedir = None
                else:
                    self.warn("Module remote_tmp %s did not exist and was "
                              "created with a mode of 0700, this may cause"
                              " issues when running as another user. To "
                              "avoid this, create the remote_tmp dir with "
                              "the correct permissions manually" % basedir)

            basefile = "ansible-moduletmp-%s-" % time.time()
            try:
                tmpdir = tempfile.mkdtemp(prefix=basefile, dir=basedir)
            except OSError as ex:
                raise Exception(
                    f"Failed to create remote module tmp path at dir {basedir!r} "
                    f"with prefix {basefile!r}.",
                ) from ex
            if not self._keep_remote_files:
                atexit.register(shutil.rmtree, tmpdir)
            self._tmpdir = tmpdir

        return self._tmpdir