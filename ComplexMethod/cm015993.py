def _validate_basic_json(self, traceEvents, cuda_available=False):
        MAX_GPU_COUNT = 8
        PROFILER_IDX = -4
        RECORD_END = -1
        RECORD_START = -2
        traceEventProfiler = traceEvents[PROFILER_IDX]

        self.assertTrue(traceEventProfiler["name"] == "PyTorch Profiler (0)")
        self.assertTrue(traceEvents[RECORD_END]["name"] == "Record Window End")
        self.assertTrue(
            traceEvents[RECORD_START]["name"] == "Iteration Start: PyTorch Profiler"
        )
        # check that the profiler starts/ends within the record interval
        self.assertGreaterEqual(
            traceEventProfiler["ts"],
            traceEvents[RECORD_START]["ts"],
            "Profiler starts before record!",
        )
        self.assertLessEqual(
            traceEventProfiler["ts"] + traceEventProfiler["dur"],
            traceEvents[RECORD_END]["ts"],
            "Profiler ends after record end!",
        )

        gpu_dict = collections.defaultdict(int)
        for i, traceEvent in enumerate(traceEvents):
            if (
                i == len(traceEvents) + RECORD_END
                or i == len(traceEvents) + RECORD_START
            ):
                continue
            # make sure all valid trace events are within the bounds of the profiler
            if "ts" in traceEvent:
                self.assertGreaterEqual(
                    traceEvent["ts"],
                    traceEventProfiler["ts"],
                    "Trace event is out of bounds",
                )
            # some python events seem to go a little past record end probably because
            # of some clock inaccuracies so just compare events ending to RECORD_END
            if "dur" in traceEvent:
                self.assertLessEqual(
                    traceEvent["ts"] + traceEvent["dur"],
                    traceEvents[RECORD_END]["ts"],
                    "Trace event ends too late!",
                )
            gpu_value = traceEvent.get("args", {}).get("labels", None)
            if gpu_value and "GPU" in gpu_value:
                gpu_dict[gpu_value] += 1
                # Max PID offset is 5M, based from pytorch/kineto include header:
                # https://github.com/pytorch/kineto/blob/8681ff11e1fa54da39023076c5c43eddd87b7a8a/libkineto/include/output_base.h#L35
                kExceedMaxPid = 5000000
                self.assertTrue(
                    traceEvents[i + 1]["args"]["sort_index"]
                    == kExceedMaxPid + int(gpu_value.split()[1])
                )