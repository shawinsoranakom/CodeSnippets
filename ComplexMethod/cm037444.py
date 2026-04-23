def monitor_engine_liveness(self) -> None:
        import ray

        while not self.manager_stopped.is_set():
            actor_run_refs = list(self.get_run_refs())
            if not actor_run_refs:
                logger.info(
                    "There are no actors to monitor currently. "
                    "The monitoring function is about to terminate."
                )
                break
            actor_done_refs, _ = ray.wait(actor_run_refs, timeout=5)
            unexpected_failure = False
            for actor_ref in actor_done_refs:
                if self.manager_stopped.is_set():
                    break
                if actor_ref not in self.get_run_refs():
                    # The run refs may have been updated by elastic scale-down.
                    continue
                try:
                    ray.get(actor_ref)
                except ray.exceptions.RayActorError:
                    self.failed_proc_name = f"Actor {actor_ref}"
                    unexpected_failure = True

            if unexpected_failure:
                break

        self.shutdown()