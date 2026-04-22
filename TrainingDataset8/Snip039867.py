def _run_script(self, rerun_data: RerunData) -> None:
        self.forward_msg_queue.clear()
        super()._run_script(rerun_data)