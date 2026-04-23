def main():
    if len(sys.argv) < 5:
        end({
            "failed": True,
            "msg": "usage: async_wrapper <jid> <time_limit> <preserve_tmp> <module_path> <invocation_args> ..."
                   "Humans, do not call directly!"
        }, 1)

    jid = "%s.%d" % (sys.argv[1], os.getpid())
    time_limit = sys.argv[2]
    preserve_tmp = sys.argv[3].lower() == 'true'
    wrapped_module = sys.argv[4]
    invocation_args = sys.argv[5:]
    step = 5

    async_dir = os.environ.get('ANSIBLE_ASYNC_DIR', '~/.ansible_async')

    # setup job output directory
    jobdir = os.path.expanduser(async_dir)
    global job_path
    job_path = os.path.join(jobdir, jid)

    try:
        # TODO: Add checks for permissions on path.
        os.makedirs(jobdir, exist_ok=True)
    except Exception as e:
        end({
            "failed": True,
            "msg": "could not create directory: %s - %s" % (jobdir, to_text(e)),
            "exception": to_text(traceback.format_exc()),  # NB: task executor compat will coerce to the correct dataclass type
        }, 1)

    # immediately exit this process, leaving an orphaned process
    # running which immediately forks a supervisory timing process

    try:
        pid = os.fork()
        if pid:
            # Notify the overlord that the async process started

            # we need to not return immediately such that the launched command has an attempt
            # to initialize PRIOR to ansible trying to clean up the launch directory (and argsfile)
            # this probably could be done with some IPC later.  Modules should always read
            # the argsfile at the very first start of their execution anyway

            # close off notifier handle in grandparent, probably unnecessary as
            # this process doesn't hang around long enough
            ipc_notifier.close()

            # allow waiting up to 2.5 seconds in total should be long enough for worst
            # loaded environment in practice.
            retries = 25
            while retries > 0:
                if ipc_watcher.poll(0.1):
                    break
                else:
                    retries = retries - 1
                    continue

            notice("Return async_wrapper task started.")
            end({"failed": False, "started": True, "finished": False, "ansible_job_id": jid, "results_file": job_path,
                 "_ansible_suppress_tmpdir_delete": (not preserve_tmp)}, 0)
        else:
            # The actual wrapper process

            # close off the receiving end of the pipe from child process
            ipc_watcher.close()

            # Daemonize, so we keep on running
            daemonize_self()

            # we are now daemonized, create a supervisory process
            notice("Starting module and watcher")

            sub_pid = os.fork()
            if sub_pid:
                # close off inherited pipe handles
                ipc_watcher.close()
                ipc_notifier.close()

                # the parent stops the process after the time limit
                remaining = int(time_limit)

                # set the child process group id to kill all children
                os.setpgid(sub_pid, sub_pid)

                notice("Start watching %s (%s)" % (sub_pid, remaining))
                time.sleep(step)
                while os.waitpid(sub_pid, os.WNOHANG) == (0, 0):
                    notice("%s still running (%s)" % (sub_pid, remaining))
                    time.sleep(step)
                    remaining = remaining - step
                    if remaining <= 0:
                        # ensure we leave response in poll location
                        res = {'msg': 'Timeout exceeded', 'failed': True, 'child_pid': sub_pid}
                        jwrite(res)

                        # actually kill it
                        notice("Timeout reached, now killing %s" % (sub_pid))
                        os.killpg(sub_pid, signal.SIGKILL)
                        notice("Sent kill to group %s " % sub_pid)
                        time.sleep(1)
                        if not preserve_tmp:
                            shutil.rmtree(os.path.dirname(wrapped_module), True)
                        end(res)
                notice("Done in kid B.")
                if not preserve_tmp:
                    shutil.rmtree(os.path.dirname(wrapped_module), True)
                end()
            else:
                # the child process runs the actual module
                notice("Start module (%s)" % os.getpid())
                _run_module(jid, *invocation_args)
                notice("Module complete (%s)" % os.getpid())

    except Exception as e:
        notice("error: %s" % e)
        end({"failed": True, "msg": "FATAL ERROR: %s" % e}, "async_wrapper exited prematurely")