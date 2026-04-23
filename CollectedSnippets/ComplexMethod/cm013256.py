def evaluate_platform_supports_fp8():
    if torch.cuda.is_available():
        if torch.version.hip:
            archs = ['gfx94']
            if ROCM_VERSION >= (6, 3):
                archs.extend(['gfx120'])
            if ROCM_VERSION >= (6, 5):
                archs.append('gfx95')
            for arch in archs:
                if arch in torch.cuda.get_device_properties(0).gcnArchName:
                    return True
            return False
        else:
            return SM90OrLater or torch.cuda.get_device_capability() == (8, 9)
    if torch.xpu.is_available():
        return True
    # As CPU supports FP8 and is always available, return True.
    return True