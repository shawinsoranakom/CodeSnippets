def _get_fps(self, mode, batch_size, gpu_num, avg_of_records, run_mode, unit=None):
        if mode == -1 and run_mode == "sp":
            assert unit, "Please set the unit when mode is -1."
            fps = gpu_num * avg_of_records
        elif mode == -1 and run_mode == "mp":
            assert unit, "Please set the unit when mode is -1."
            fps = gpu_num * avg_of_records  # temporarily, not used now
            print("------------this is mp")
        elif mode == 0:
            # s/step -> samples/s
            fps = (batch_size * gpu_num) / avg_of_records
            unit = "samples/s"
        elif mode == 1:
            # steps/s -> steps/s
            fps = avg_of_records
            unit = "steps/s"
        elif mode == 2:
            # s/step -> steps/s
            fps = 1 / avg_of_records
            unit = "steps/s"
        elif mode == 3:
            # steps/s -> samples/s
            fps = batch_size * gpu_num * avg_of_records
            unit = "samples/s"
        elif mode == 4:
            # s/epoch -> s/epoch
            fps = avg_of_records
            unit = "s/epoch"
        else:
            ValueError("Unsupported analysis mode.")

        return fps, unit