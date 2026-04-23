def _run_child(self, child, terminal_input):
        r, w = os.pipe()  # Pipe test results from child back to parent
        try:
            pid, fd = pty.fork()
        except (OSError, AttributeError) as e:
            os.close(r)
            os.close(w)
            self.skipTest("pty.fork() raised {}".format(e))
            raise

        if pid == 0:
            # Child
            try:
                os.close(r)
                with open(w, "w") as wpipe:
                    child(wpipe)
            except:
                traceback.print_exc()
            finally:
                # We don't want to return to unittest...
                os._exit(0)

        # Parent
        os.close(w)
        os.write(fd, terminal_input)

        # Get results from the pipe
        with open(r, encoding="utf-8") as rpipe:
            lines = []
            while True:
                line = rpipe.readline().strip()
                if line == "":
                    # The other end was closed => the child exited
                    break
                lines.append(line)

        # Check the result was got and corresponds to the user's terminal input
        if len(lines) != 2:
            # Something went wrong, try to get at stderr
            # Beware of Linux raising EIO when the slave is closed
            child_output = bytearray()
            while True:
                try:
                    chunk = os.read(fd, 3000)
                except OSError:  # Assume EIO
                    break
                if not chunk:
                    break
                child_output.extend(chunk)
            os.close(fd)
            child_output = child_output.decode("ascii", "ignore")
            self.fail("got %d lines in pipe but expected 2, child output was:\n%s"
                      % (len(lines), child_output))

        # bpo-40155: Close the PTY before waiting for the child process
        # completion, otherwise the child process hangs on AIX.
        os.close(fd)

        support.wait_process(pid, exitcode=0)

        return lines