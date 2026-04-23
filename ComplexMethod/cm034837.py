def analysis(
        self, batch_size, gpu_num=1, skip_steps=0, mode=-1, run_mode="sp", unit=None
    ):
        if batch_size <= 0:
            print("base_batch_size should larger than 0.")
            return 0, ""

        if (
            len(self.records) <= skip_steps
        ):  # to address the condition which item of log equals to skip_steps
            print("no records")
            return 0, ""

        sum_of_records = 0
        sum_of_records_skipped = 0
        skip_min = self.records[skip_steps]
        skip_max = self.records[skip_steps]

        count = len(self.records)
        for i in range(count):
            sum_of_records += self.records[i]
            if i >= skip_steps:
                sum_of_records_skipped += self.records[i]
                if self.records[i] < skip_min:
                    skip_min = self.records[i]
                if self.records[i] > skip_max:
                    skip_max = self.records[i]

        avg_of_records = sum_of_records / float(count)
        avg_of_records_skipped = sum_of_records_skipped / float(count - skip_steps)

        fps, fps_unit = self._get_fps(
            mode, batch_size, gpu_num, avg_of_records, run_mode, unit
        )
        fps_skipped, _ = self._get_fps(
            mode, batch_size, gpu_num, avg_of_records_skipped, run_mode, unit
        )
        if mode == -1:
            print("average ips of %d steps, skip 0 step:" % count)
            print("\tAvg: %.3f %s" % (avg_of_records, fps_unit))
            print("\tFPS: %.3f %s" % (fps, fps_unit))
            if skip_steps > 0:
                print("average ips of %d steps, skip %d steps:" % (count, skip_steps))
                print("\tAvg: %.3f %s" % (avg_of_records_skipped, fps_unit))
                print("\tMin: %.3f %s" % (skip_min, fps_unit))
                print("\tMax: %.3f %s" % (skip_max, fps_unit))
                print("\tFPS: %.3f %s" % (fps_skipped, fps_unit))
        elif mode == 1 or mode == 3:
            print("average latency of %d steps, skip 0 step:" % count)
            print("\tAvg: %.3f steps/s" % avg_of_records)
            print("\tFPS: %.3f %s" % (fps, fps_unit))
            if skip_steps > 0:
                print(
                    "average latency of %d steps, skip %d steps:" % (count, skip_steps)
                )
                print("\tAvg: %.3f steps/s" % avg_of_records_skipped)
                print("\tMin: %.3f steps/s" % skip_min)
                print("\tMax: %.3f steps/s" % skip_max)
                print("\tFPS: %.3f %s" % (fps_skipped, fps_unit))
        elif mode == 0 or mode == 2:
            print("average latency of %d steps, skip 0 step:" % count)
            print("\tAvg: %.3f s/step" % avg_of_records)
            print("\tFPS: %.3f %s" % (fps, fps_unit))
            if skip_steps > 0:
                print(
                    "average latency of %d steps, skip %d steps:" % (count, skip_steps)
                )
                print("\tAvg: %.3f s/step" % avg_of_records_skipped)
                print("\tMin: %.3f s/step" % skip_min)
                print("\tMax: %.3f s/step" % skip_max)
                print("\tFPS: %.3f %s" % (fps_skipped, fps_unit))

        return round(fps_skipped, 3), fps_unit