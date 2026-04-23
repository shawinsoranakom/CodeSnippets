def test_proper_exit(self):
        """There might be ConnectionResetError or leaked semaphore warning
        (due to dirty process exit), but they are all safe to ignore"""

        # TODO: test the case where the pin_memory_thread triggers an
        #       error/fatal signal. I haven't found out how to properly do that.

        for (
            is_iterable_dataset,
            use_workers,
            pin_memory,
            hold_iter_reference,
        ) in itertools.product([True, False], repeat=4):
            # `hold_iter_reference` specifies whether we hold a reference to the
            # iterator. This is interesting because Python3 error traces holds a
            # reference to the frames, which hold references to all the local
            # variables including the iterator, and then the iterator dtor may
            # not be called before process end. It is important to see that the
            # processes still exit in both cases.

            if pin_memory and (not TEST_CUDA or IS_WINDOWS):
                # This test runs in a subprocess, which can only initialize CUDA with spawn.
                # DataLoader with pin_memory=True initializes CUDA when its iterator is constructed.
                # For windows, pin_memory sometimes causes CUDA oom.
                continue

            # `exit_method` controls the way the loader process ends.
            #   - `*_kill` means that `*` is killed by OS.
            #   - `*_error` means that `*` raises an error.
            #   - `None` means that no error happens.
            # In all cases, all processes should end properly.
            if use_workers:
                # TODO: Fix test for 'loader_kill' that would cause running out of shared memory.
                # Killing loader process would prevent DataLoader iterator clean up all queues
                # and worker processes
                exit_methods = [None, "loader_error", "worker_error", "worker_kill"]
                persistent_workers = self.persistent_workers
            else:
                exit_methods = [None, "loader_error", "loader_kill"]
                persistent_workers = False

            for exit_method in exit_methods:
                if exit_method == "worker_kill":
                    # FIXME: This sometimes hangs. See #16608.
                    continue

                desc = []
                desc.append(f"is_iterable_dataset={is_iterable_dataset}")
                desc.append(f"use_workers={use_workers}")
                desc.append(f"pin_memory={pin_memory}")
                desc.append(f"hold_iter_reference={hold_iter_reference}")
                desc.append(f"exit_method={exit_method}")
                desc = "test_proper_exit with " + ", ".join(desc)

                # Event that the loader process uses to signal testing process
                # that various things are setup, including that the worker pids
                # are specified in `worker_pids` array.
                loader_setup_event = mp.Event()

                # Event that this process has finished setting up, and the
                # loader process can now proceed to trigger error events or
                # finish normally.
                tester_setup_event = mp.Event()

                loader_p = ErrorTrackingProcess(
                    target=_test_proper_exit,
                    args=(
                        is_iterable_dataset,
                        use_workers,
                        pin_memory,
                        exit_method,
                        hold_iter_reference,
                        loader_setup_event,
                        tester_setup_event,
                        persistent_workers,
                    ),
                    disable_stderr=False,
                )
                loader_p.start()
                loader_psutil_p = psutil.Process(loader_p.pid)

                # Wait for loader process to set everything up, e.g., starting
                # workers.
                loader_setup_event.wait(timeout=JOIN_TIMEOUT)
                if not loader_setup_event.is_set():
                    fail_msg = (
                        desc + ": loader process failed to setup within given time"
                    )
                    if loader_p.exception is not None:
                        fail_msg += f", and had exception {loader_p.exception}"
                    elif not loader_p.is_alive():
                        fail_msg += f", and exited with code {loader_p.exitcode} but had no exception"
                    else:
                        fail_msg += ", and is still alive."
                    if loader_p.is_alive():
                        # this may kill the process, needs to run after the above lines
                        loader_p.print_traces_of_all_threads()
                    self.fail(fail_msg)

                # We are certain that the workers have started now.
                worker_psutil_ps = loader_psutil_p.children()

                def fail(reason):
                    report_psutil_attrs = [
                        "pid",
                        "name",
                        "cpu_times",
                        "io_counters",
                        "memory_full_info",
                        "num_ctx_switches",
                        "open_files",
                        "threads",
                        "status",
                        "nice",
                        "ionice",
                    ]
                    if reason is None:
                        err_msg = desc
                    else:
                        err_msg = f"{desc}: {reason}"
                    err_msg += "\nLoader info:\n\t"
                    if loader_psutil_p.is_running():
                        err_msg += str(
                            loader_psutil_p.as_dict(attrs=report_psutil_attrs)
                        )
                        # this may kill the process, needs to run after the above line
                        loader_p.print_traces_of_all_threads()
                    else:
                        err_msg += f"exited with code {loader_p.exitcode}"
                    if use_workers:
                        err_msg += "\nWorker(s) info:"
                        for idx, worker_psutil_p in enumerate(worker_psutil_ps):
                            err_msg += f"\n\tWorker {idx}:\n\t\t"
                            if worker_psutil_p.is_running():
                                err_msg += str(
                                    worker_psutil_p.as_dict(attrs=report_psutil_attrs)
                                )
                                # this may kill the process, needs to run after the above line
                                print_traces_of_all_threads(worker_psutil_p.pid)
                            else:
                                err_msg += "exited with unknown code"
                    self.fail(err_msg)

                tester_setup_event.set()

                try:
                    loader_p.join(JOIN_TIMEOUT + MP_STATUS_CHECK_INTERVAL)
                    if loader_p.is_alive():
                        fail_reason = "loader process did not terminate"
                        if loader_p.exception is not None:
                            fail(
                                fail_reason
                                + f", and had exception {loader_p.exception}"
                            )
                        else:
                            fail(fail_reason + ", and had no exception")
                    _, alive = psutil.wait_procs(
                        worker_psutil_ps,
                        timeout=(MP_STATUS_CHECK_INTERVAL + JOIN_TIMEOUT),
                    )
                    if len(alive) > 0:
                        fail(
                            "worker process (pid(s) {}) did not terminate".format(
                                ", ".join(str(p.pid) for p in alive)
                            )
                        )
                    if exit_method is None:
                        if loader_p.exitcode != 0:
                            fail(
                                f"loader process had nonzero exitcode {loader_p.exitcode}"
                            )
                    else:
                        if loader_p.exitcode == 0:
                            fail("loader process had zero exitcode")
                        if exit_method == "loader_error":
                            if not isinstance(
                                loader_p.exception, RuntimeError
                            ) or "Loader error" not in str(loader_p.exception):
                                fail(
                                    f"loader process did not raise expected exception, but had {loader_p.exception}"
                                )
                        elif exit_method == "worker_kill":
                            if isinstance(loader_p.exception, RuntimeError):
                                if "DataLoader worker (pid" not in str(
                                    loader_p.exception
                                ):
                                    fail(
                                        f"loader process did not raise expected exception, but had {loader_p.exception}"
                                    )
                            elif isinstance(loader_p.exception, ConnectionRefusedError):
                                # Sometimes, when the worker is being killed and is freeing its
                                # resources, the unpickling in loader process will be met an
                                # a `ConnectionRefusedError` as it can not open a socket to receive
                                # resource. In such cases, the worker may not have fully exited,
                                # and the loader can't know this via `is_alive` check or `SIGCHLD`
                                # handler. So we permit this as an allowed error as well.
                                # After all, we are happy as long as it terminates.
                                pass
                            else:
                                fail(
                                    f"loader process did not raise expected exception, but had {loader_p.exception}"
                                )
                        elif exit_method == "worker_error":
                            if not isinstance(
                                loader_p.exception, RuntimeError
                            ) or "Worker error" not in str(loader_p.exception):
                                fail(
                                    f"loader process did not raise expected exception, but had {loader_p.exception}"
                                )
                finally:
                    loader_p.terminate()