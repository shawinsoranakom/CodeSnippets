def daemonize(module, cmd):
    """
    Execute a command while detaching as a daemon, returns rc, stdout, and stderr.

    :arg module: is an AnsibleModule object, used for it's utility methods
    :arg cmd: is a list or string representing the command and options to run

    This is complex because daemonization is hard for people.
    What we do is daemonize a part of this module, the daemon runs the command,
    picks up the return code and output, and returns it to the main process.
    """

    # init some vars
    chunk = 4096  # FIXME: pass in as arg?
    errors = 'surrogate_or_strict'

    # start it!
    try:
        pipe = os.pipe()
        pid = fork_process()
    except (OSError, RuntimeError):
        module.fail_json(msg="Error while attempting to fork.")
    except Exception as exc:
        module.fail_json(msg=to_text(exc))

    # we don't do any locking as this should be a unique module/process
    if pid == 0:
        os.close(pipe[0])

        if not isinstance(cmd, list):
            cmd = shlex.split(to_text(cmd, errors=errors))

        # make sure we always use byte strings
        run_cmd = []
        for c in cmd:
            run_cmd.append(to_bytes(c, errors=errors))

        # execute the command in forked process
        p = subprocess.Popen(run_cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=lambda: os.close(pipe[1]))
        fds = [p.stdout, p.stderr]

        # loop reading output till it is done
        output = {p.stdout: b"", p.stderr: b""}
        while fds:
            rfd, wfd, efd = select.select(fds, [], fds, 1)
            if (rfd + wfd + efd) or p.poll() is None:
                for out in list(fds):
                    if out in rfd:
                        data = os.read(out.fileno(), chunk)
                        if data:
                            output[out] += to_bytes(data, errors=errors)
                        else:
                            fds.remove(out)
            else:
                break

        # even after fds close, we might want to wait for pid to die
        p.wait()

        # Return a pickled data of parent
        return_data = pickle.dumps([p.returncode, to_text(output[p.stdout]), to_text(output[p.stderr])], protocol=pickle.HIGHEST_PROTOCOL)
        os.write(pipe[1], to_bytes(return_data, errors=errors))

        # clean up
        os.close(pipe[1])
        os._exit(0)

    elif pid == -1:
        module.fail_json(msg="Unable to fork, no exception thrown, probably due to lack of resources, check logs.")

    else:
        # in parent
        os.close(pipe[1])
        os.waitpid(pid, 0)

        # Grab response data after child finishes
        return_data = b""
        while True:
            rfd, wfd, efd = select.select([pipe[0]], [], [pipe[0]])
            if pipe[0] in rfd:
                data = os.read(pipe[0], chunk)
                if not data:
                    break
                return_data += to_bytes(data, errors=errors)

        return pickle.loads(to_bytes(return_data, errors=errors))