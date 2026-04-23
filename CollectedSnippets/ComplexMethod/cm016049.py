def _force_shutdown(self, verbose: bool = False) -> None:
        """Try to interrupt jobs, and kill if need be.
        We would prefer to softly terminate jobs so that they have a chance to
        clean up before shutting down.
        """
        for job in self._active_jobs:
            job.proc.interrupt()

        if verbose and self._currently_processed is not None:
            print(
                textwrap.dedent(
                    f"""
                Failed when processing the following Job:
                  Label:      {self._currently_processed.label}
                  AutoLabels: {self._currently_processed.autolabels}
                  Source cmd: {self._currently_processed.source_cmd}
            """
                ).strip()
                + "\n"
            )

        if self._active_jobs:
            time.sleep(0.5)

        remaining_jobs = [j for j in self._active_jobs if j.proc.poll() is None]
        if remaining_jobs:
            print(
                f"SIGINT sent to {len(self._active_jobs)} jobs, "
                f"{len(remaining_jobs)} have not yet exited.\n"
                "Entering short cleanup loop, after which stragglers will "
                "be forcibly terminated."
            )

            for _ in range(5):
                time.sleep(2.0)
                remaining_jobs = [j for j in remaining_jobs if j.proc.poll() is None]
                if remaining_jobs:
                    print(f"{len(remaining_jobs)} still remain.")
                else:
                    print("All remaining jobs have gracefully terminated.")
                    return

            print(f"{len(remaining_jobs)} jobs refused to exit. Forcibly terminating.")
            for j in remaining_jobs:
                j.proc.terminate()