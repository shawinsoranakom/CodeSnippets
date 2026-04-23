def run_single_proc(self, command, num_lines_to_read=4):
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,
        )

        output = self.read_process_output(proc, num_lines_to_read)

        try:
            os.kill(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            # The process may have exited already. If so, we don't need to do anything
            pass

        return output