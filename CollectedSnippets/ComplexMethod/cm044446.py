def __call__(self):
        """Output the latest test stats"""
        if self._data.has_oom:
            return

        self._write(self._header_row)
        self._write(["Batch Size"] + [str(int(b)) for b in self._data.batch_sizes[-1]])
        egs = [f"{e:.1f}" for e in self._data.get_samples(-1) / self._run_time]
        avg_egs = [f"{(self._data.get_samples_stats('mean', -1) / self._run_time):.1f}"]
        min_egs = [f"{(self._data.get_samples_stats('min', -1) / self._run_time):.1f}"]
        self._write(["EG/S"] + egs + avg_egs + min_egs)

        if self._data.has_detector and self._data.face_scaling > 1:
            lbl = [f"Scaled EG/S ({self._data.face_scaling}x)"]
            egs = [f"{e:.1f}" for e in self._data.get_samples(-1, adjusted=True) / self._run_time]
            avg_egs = [
                f"{self._data.get_samples_stats('mean', -1, adjusted=True) / self._run_time:.1f}"]
            min_egs = [
                f"{self._data.get_samples_stats('min', -1, adjusted=True) / self._run_time:.1f}"]
            self._write(lbl + egs + avg_egs + min_egs)

        vram_alloc, vram_res = (str(int(round(v / 1024 / 1024))) for v in self._data.vram[-1])
        vram_res = f"{vram_res}/{str(int(round(self._data.vram_limit / 1024 / 1024)))}"
        self._write(["VRAM(MB) Allocated", vram_alloc], left_justify=True)
        self._write(["VRAM(MB) Reserved", vram_res], left_justify=True)

        line = "-" * (sum(self._label_widths) + (len(self._label_widths) - 2))
        tqdm.write(f"{self._spacer}{line}")