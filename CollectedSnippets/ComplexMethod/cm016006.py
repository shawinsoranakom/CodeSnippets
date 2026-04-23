def check_trace(self, expected, mem=False) -> None:
        blueprint("verifying trace")
        event_list = CppThreadTestXPU.TraceObject.events()
        for key, values in expected.items():
            count = values[0]
            min_count = count * (ActivateIteration - 1)
            device = values[1]
            filtered = filter(
                lambda ev: ev.name == key
                and str(ev.device_type) == f"DeviceType.{device}",
                event_list,
            )

            if mem:
                actual = 0
                for ev in filtered:
                    sev = str(ev)
                    has_cuda_memory_usage = (
                        sev.find("xpu_memory_usage=0 ") < 0
                        and sev.find("xpu_memory_usage=") > 0
                    )
                    if has_cuda_memory_usage:
                        actual += 1
                self.assert_text(
                    actual >= min_count,
                    f"{key}: {actual} >= {min_count}",
                    "not enough event with xpu_memory_usage set",
                )
            else:
                actual = len(list(filtered))
                if count == 1:  # test_without
                    count *= ActivateIteration
                    self.assert_text(
                        actual == count,
                        f"{key}: {actual} == {count}",
                        "baseline event count incorrect",
                    )
                else:
                    self.assert_text(
                        actual >= min_count,
                        f"{key}: {actual} >= {min_count}",
                        "not enough event recorded",
                    )