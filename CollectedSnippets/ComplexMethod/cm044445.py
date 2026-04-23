def _output_stats(self) -> None:
        """Print the benchmark results to screen in a format that is easy to read and can be
        copy and pasted (fixed width)"""
        egs = [(i * b) / self._run_time for i, b in zip(self.iterations, self.batch_sizes)]
        bs_str = [str(i) for i in self.batch_sizes]
        eg_str = ["N/A" if i < 0 else f"{i:.1f}" for i in egs]
        vram_alloc_str = ["N/A" if i < 0 else str(int(round(i / (1024 * 1024))))
                          for i in self.vram[0]]
        vram_res_str = ["N/A" if i < 0 else str(int(round(i / (1024 * 1024))))
                        for i in self.vram[1]]
        labels = ["BatchSize", "EG/S", "VRAM(MB) Allocated", "VRAM(MB) Reserved"]

        lbl_width = max(len(i) for i in labels)
        col_width = max(len(i) for i in bs_str + eg_str + vram_alloc_str + vram_res_str) + 2

        for lbl, data in zip(labels, (bs_str, eg_str, vram_alloc_str, vram_res_str)):
            dat = "".join([d.rjust(col_width) for d in data])
            print(f"    {lbl.ljust(lbl_width)}{dat}")