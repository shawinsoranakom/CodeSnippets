def max_clock_rate():
    """
    unit: MHz
    """
    if not torch.version.hip:
        from triton.testing import nvsmi

        return nvsmi(["clocks.max.sm"])[0]
    else:
        # Manually set max-clock speeds on ROCm until equivalent nvmsi
        # functionality in triton.testing or via pyamdsmi enablement. Required
        # for test_snode_runtime unit tests.
        gcn_arch = str(torch.cuda.get_device_properties(0).gcnArchName.split(":", 1)[0])
        if "gfx94" in gcn_arch:
            return 1700
        elif "gfx90a" in gcn_arch:
            return 1700
        elif "gfx908" in gcn_arch:
            return 1502
        elif "gfx12" in gcn_arch:
            return 1700
        elif "gfx11" in gcn_arch:
            return 1700
        elif "gfx103" in gcn_arch:
            return 1967
        elif "gfx101" in gcn_arch:
            return 1144
        elif "gfx95" in gcn_arch:
            return 1700  # TODO: placeholder, get actual value
        else:
            return 1100