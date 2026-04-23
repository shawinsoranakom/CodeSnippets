def test_distributed(test_module, test_directory, options):
    mpi_available = shutil.which("mpiexec")
    if options.verbose and not mpi_available:
        print_to_stderr("MPI not available -- MPI backend tests will be skipped")

    config = DISTRIBUTED_TESTS_CONFIG
    for backend, env_vars in config.items():
        if sys.platform == "win32" and backend != "gloo":
            continue
        if backend == "mpi" and not mpi_available:
            continue
        for with_init_file in {True, False}:
            if sys.platform == "win32" and not with_init_file:
                continue
            tmp_dir = tempfile.mkdtemp()
            init_method = "file" if with_init_file else "env"
            if options.verbose:
                with_init = f"with {init_method} init_method"
                print_to_stderr(
                    f"Running distributed tests for the {backend} backend {with_init}"
                )
            old_environ = dict(os.environ)
            os.environ["TEMP_DIR"] = tmp_dir
            os.environ["BACKEND"] = backend
            os.environ.update(env_vars)
            report_tag = f"dist-{backend}" if backend != "test" else ""
            report_tag += f"-init-{init_method}"
            os.environ["TEST_REPORT_SOURCE_OVERRIDE"] = report_tag
            try:
                os.mkdir(os.path.join(tmp_dir, "barrier"))
                os.mkdir(os.path.join(tmp_dir, "test_dir"))
                if backend == "mpi":
                    # test mpiexec for --noprefix option
                    with open(os.devnull, "w") as devnull:
                        allowrunasroot_opt = (
                            "--allow-run-as-root"
                            if subprocess.call(
                                'mpiexec --allow-run-as-root -n 1 bash -c ""',
                                shell=True,
                                stdout=devnull,
                                stderr=subprocess.STDOUT,
                            )
                            == 0
                            else ""
                        )
                        noprefix_opt = (
                            "--noprefix"
                            if subprocess.call(
                                f'mpiexec {allowrunasroot_opt} -n 1 --noprefix bash -c ""',
                                shell=True,
                                stdout=devnull,
                                stderr=subprocess.STDOUT,
                            )
                            == 0
                            else ""
                        )

                    mpiexec = ["mpiexec", "-n", "3", noprefix_opt, allowrunasroot_opt]

                    return_code = run_test(
                        test_module, test_directory, options, launcher_cmd=mpiexec
                    )
                else:
                    return_code = run_test(
                        test_module,
                        test_directory,
                        options,
                        extra_unittest_args=["--subprocess"],
                    )
                if return_code != 0:
                    return return_code
            finally:
                shutil.rmtree(tmp_dir)
                os.environ.clear()
                os.environ.update(old_environ)
    return 0