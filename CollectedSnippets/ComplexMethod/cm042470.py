def build(cls, code_export_dir, with_cython=False, cmake_builder: CMakeBuilder = None, verbose: bool = True):
        # Compile solver
        cwd = os.getcwd()
        os.chdir(code_export_dir)
        if with_cython:
            call(
                ['make', 'clean_sim_cython'],
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
            call(
                ['make', 'sim_cython'],
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
        else:
            if cmake_builder is not None:
                cmake_builder.exec(code_export_dir, verbose=verbose)
            else:
                call(
                    ['make', 'sim_shared_lib'],
                    stdout=None if verbose else DEVNULL,
                    stderr=None if verbose else STDOUT
                )
        os.chdir(cwd)