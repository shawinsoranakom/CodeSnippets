def test_jit_cuda_archflags(self):
        # Test a number of combinations:
        #   - the default for the machine we're testing on
        #   - Separators, can be ';' (most common) or ' '
        #   - Architecture names
        #   - With/without '+PTX'

        n = torch.cuda.device_count()
        capabilities = {torch.cuda.get_device_capability(i) for i in range(n)}
        # expected values is length-2 tuple: (list of ELF, list of PTX)
        # note: there should not be more than one PTX value
        archflags = {
            "": (
                [f"{capability[0]}{capability[1]}" for capability in capabilities],
                None,
            ),
        }
        archflags["7.5+PTX"] = (["75"], ["75"])
        major, minor = map(int, torch.version.cuda.split(".")[:2])
        if major < 12 or (major == 12 and minor <= 9):
            # Compute capability <= 7.0 is only supported up to CUDA 12.9
            archflags["Maxwell+Tegra;6.1"] = (["53", "61"], None)
            archflags["Volta"] = (["70"], ["70"])
            archflags["5.0;6.0+PTX;7.0;7.5"] = (["50", "60", "70", "75"], ["60"])
        if major < 12:
            # CUDA 12 drops compute capability < 5.0
            archflags["Pascal 3.5"] = (["35", "60", "61"], None)

        for flags, expected in archflags.items():
            try:
                self._run_jit_cuda_archflags(flags, expected)
            except RuntimeError as e:
                # Using the device default (empty flags) may fail if the device is newer than the CUDA compiler
                # This raises a RuntimeError with a specific message which we explicitly ignore here
                if not flags and "Error building" in str(e):
                    pass
                else:
                    raise
            try:
                torch.cuda.synchronize()
            except RuntimeError:
                # Ignore any error, e.g. unsupported PTX code on current device
                # to avoid errors from here leaking into other tests
                pass