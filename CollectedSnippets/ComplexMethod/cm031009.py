def accumulate_result(self, result: TestResult, runtests: RunTests) -> None:
        test_name = result.test_name
        rerun = runtests.rerun
        fail_env_changed = runtests.fail_env_changed

        match result.state:
            case State.PASSED:
                self.good.append(test_name)
            case State.ENV_CHANGED:
                self.env_changed.append(test_name)
                self.rerun_results.append(result)
            case State.SKIPPED:
                self.skipped.append(test_name)
            case State.RESOURCE_DENIED:
                self.resource_denied.append(test_name)
            case State.INTERRUPTED:
                self.interrupted = True
            case State.DID_NOT_RUN:
                self.run_no_tests.append(test_name)
            case _:
                if result.is_failed(fail_env_changed):
                    self.bad.append(test_name)
                    self.rerun_results.append(result)
                else:
                    raise ValueError(f"invalid test state: {result.state!r}")

        if result.state == State.WORKER_BUG:
            self.worker_bug = True

        if result.has_meaningful_duration() and not rerun:
            if result.duration is None:
                raise ValueError("result.duration is None")
            self.test_times.append((result.duration, test_name))
        if result.stats is not None:
            self.stats.accumulate(result.stats)
        if rerun:
            self.rerun.append(test_name)
        if result.covered_lines:
            # we don't care about trace counts so we don't have to sum them up
            self.covered_lines.update(result.covered_lines)
        xml_data = result.xml_data
        if xml_data:
            self.add_junit(xml_data)