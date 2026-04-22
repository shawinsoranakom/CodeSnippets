def run_double_proc(
        self, command_one, command_two, wait_in_seconds=2, num_lines_to_read=4
    ):
        proc_one = subprocess.Popen(
            command_one,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,
        )

        # Getting the output from process one ensures the process started first
        output_one = self.read_process_output(proc_one, num_lines_to_read)

        proc_two = subprocess.Popen(
            command_two,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setpgrp,
        )

        output_two = self.read_process_output(proc_two, num_lines_to_read)

        try:
            os.killpg(os.getpgid(proc_one.pid), signal.SIGKILL)
            os.killpg(os.getpgid(proc_two.pid), signal.SIGKILL)
        except ProcessLookupError:
            # The process may have exited already. If so, we don't need to do anything
            pass

        return output_one, output_two