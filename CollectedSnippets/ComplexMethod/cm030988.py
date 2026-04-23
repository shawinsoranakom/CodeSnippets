def get_temp_dir(tmp_dir: StrPath | None = None) -> StrPath:
    if tmp_dir:
        tmp_dir = os.path.expanduser(tmp_dir)
    else:
        # When tests are run from the Python build directory, it is best practice
        # to keep the test files in a subfolder.  This eases the cleanup of leftover
        # files using the "make distclean" command.
        if sysconfig.is_python_build():
            if not support.is_wasi:
                tmp_dir = sysconfig.get_config_var('abs_builddir')
                if tmp_dir is None:
                    tmp_dir = sysconfig.get_config_var('abs_srcdir')
                    if not tmp_dir:
                        # gh-74470: On Windows, only srcdir is available. Using
                        # abs_builddir mostly matters on UNIX when building
                        # Python out of the source tree, especially when the
                        # source tree is read only.
                        tmp_dir = sysconfig.get_config_var('srcdir')
                        if not tmp_dir:
                            raise RuntimeError(
                                "Could not determine the correct value for tmp_dir"
                            )
                tmp_dir = os.path.join(tmp_dir, 'build')
            else:
                # WASI platform
                tmp_dir = sysconfig.get_config_var('projectbase')
                if not tmp_dir:
                    raise RuntimeError(
                        "sysconfig.get_config_var('projectbase') "
                        f"unexpectedly returned {tmp_dir!r} on WASI"
                    )
                tmp_dir = os.path.join(tmp_dir, 'build')
        else:
            tmp_dir = tempfile.gettempdir()

    return os.path.abspath(tmp_dir)