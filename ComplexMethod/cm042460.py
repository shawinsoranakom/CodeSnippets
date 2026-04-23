def build(cls, code_export_dir, with_cython=False, cmake_builder: CMakeBuilder = None, verbose: bool = True):
        """
        Builds the code for an acados OCP solver, that has been generated in code_export_dir
            :param code_export_dir: directory in which acados OCP solver has been generated, see generate()
            :param with_cython: option indicating if the cython interface is build, default: False.
            :param cmake_builder: type :py:class:`~acados_template.builders.CMakeBuilder` generate a `CMakeLists.txt` and use
                   the `CMake` pipeline instead of a `Makefile` (`CMake` seems to be the better option in conjunction with
                   `MS Visual Studio`); default: `None`
            :param verbose: indicating if build command is printed
        """
        code_export_dir = os.path.abspath(code_export_dir)
        cwd = os.getcwd()
        os.chdir(code_export_dir)
        if with_cython:
            call(
                ['make', 'clean_all'],
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
            call(
                ['make', 'ocp_cython'],
                stdout=None if verbose else DEVNULL,
                stderr=None if verbose else STDOUT
            )
        else:
            if cmake_builder is not None:
                cmake_builder.exec(code_export_dir)
            else:
                call(
                    ['make', 'clean_ocp_shared_lib'],
                    stdout=None if verbose else DEVNULL,
                    stderr=None if verbose else STDOUT
                )
                call(
                    ['make', 'ocp_shared_lib'],
                    stdout=None if verbose else DEVNULL,
                    stderr=None if verbose else STDOUT
                )
        os.chdir(cwd)