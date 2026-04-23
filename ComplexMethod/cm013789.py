def export_memory_timeline(self, path: str, device: str | None = None) -> None:
        """Export memory event information from the profiler collected
        tree for a given device, and export a timeline plot. There are 3
        exportable files using ``export_memory_timeline``, each controlled by the
        ``path``'s suffix.

        - For an HTML compatible plot, use the suffix ``.html``, and a memory timeline
          plot will be embedded as a PNG file in the HTML file.

        - For plot points consisting of ``[times, [sizes by category]]``, where
          ``times`` are timestamps and ``sizes`` are memory usage for each category.
          The memory timeline plot will be saved a JSON (``.json``) or gzipped JSON
          (``.json.gz``) depending on the suffix.

        - For raw memory points, use the suffix ``.raw.json.gz``. Each raw memory
          event will consist of ``(timestamp, action, numbytes, category)``, where
          ``action`` is one of ``[PREEXISTING, CREATE, INCREMENT_VERSION, DESTROY]``,
          and ``category`` is one of the enums from
          ``torch.profiler._memory_profiler.Category``.

        Output: Memory timeline written as gzipped JSON, JSON, or HTML.

        .. deprecated::
            ``export_memory_timeline`` is deprecated and will be removed in a future version.
            Please use ``torch.cuda.memory._record_memory_history`` and
            ``torch.cuda.memory._export_memory_snapshot`` instead.
        """
        # Default to device 0, if unset. Fallback on cpu.
        if device is None:
            if self.use_device and self.use_device != "cuda":
                device = self.use_device + ":0"
            else:
                device = "cuda:0" if torch.cuda.is_available() else "cpu"

        # Construct the memory timeline plot data
        self.mem_tl = MemoryProfileTimeline(self._memory_profile())

        # Depending on the file suffix, save the data as json.gz or json.
        # For html, we can embed the image into an HTML file.
        if path.endswith(".html"):
            self.mem_tl.export_memory_timeline_html(path, device)
        elif path.endswith(".gz"):
            with tempfile.NamedTemporaryFile("w+t", suffix=".json") as fp:
                if path.endswith("raw.json.gz"):
                    self.mem_tl.export_memory_timeline_raw(fp.name, device)
                else:
                    self.mem_tl.export_memory_timeline(fp.name, device)
                with open(fp.name) as fin, gzip.open(path, "wt") as fout:
                    fout.writelines(fin)
        else:
            self.mem_tl.export_memory_timeline(path, device)