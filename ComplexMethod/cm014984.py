def blaslt_supported_device():
    if torch.cuda.is_available():
        if torch.version.hip:
            ROCM_VERSION = tuple(int(v) for v in torch.version.hip.split('.')[:2])
            archs = ['gfx90a', 'gfx94']
            if ROCM_VERSION >= (6, 3):
                archs.extend(['gfx110', 'gfx120'])
            if ROCM_VERSION >= (6, 5):
                archs.append('gfx95')
            for arch in archs:
                if arch in torch.cuda.get_device_properties(0).gcnArchName:
                    return True
        else:
            return True
    return False