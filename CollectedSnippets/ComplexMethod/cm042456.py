def exec(self, code_export_directory, verbose=True):
        """
        Execute the compilation using `CMake` with the given settings.
        :param code_export_directory: must be the absolute path to the directory where the code was exported to
        """
        if(os.path.isabs(code_export_directory) is False):
            print(f'(W) the code export directory "{code_export_directory}" is not an absolute path!')
        self._source_dir = code_export_directory
        self._build_dir = os.path.abspath(self.build_dir)
        try:
            os.mkdir(self._build_dir)
        except FileExistsError as e:
            pass

        try:
            os.chdir(self._build_dir)
            cmd_str = self.get_cmd1_cmake()
            print(f'call("{cmd_str})"')
            retcode = call(
                cmd_str,
                shell=True,
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
            if retcode != 0:
                raise RuntimeError(f'CMake command "{cmd_str}" was terminated by signal {retcode}')
            cmd_str = self.get_cmd2_build()
            print(f'call("{cmd_str}")')
            retcode = call(
                cmd_str,
                shell=True,
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
            if retcode != 0:
                raise RuntimeError(f'Build command "{cmd_str}" was terminated by signal {retcode}')
            cmd_str = self.get_cmd3_install()
            print(f'call("{cmd_str}")')
            retcode = call(
                cmd_str,
                shell=True,
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
            if retcode != 0:
                raise RuntimeError(f'Install command "{cmd_str}" was terminated by signal {retcode}')
        except OSError as e:
            print("Execution failed:", e, file=sys.stderr)
        except Exception as e:
            print("Execution failed:", e, file=sys.stderr)
            exit(1)