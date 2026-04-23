def get_device():
    device_mode = os.getenv('MINERU_DEVICE_MODE', None)
    if device_mode is not None:
        return device_mode
    else:
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            try:
                if torch_npu.npu.is_available():
                    return "npu"
            except Exception as e:
                try:
                    if torch.gcu.is_available():
                        return "gcu"
                except Exception as e:
                    try:
                        if torch.musa.is_available():
                            return "musa"
                    except Exception as e:
                        try:
                            if torch.mlu.is_available():
                                return "mlu"
                        except Exception as e:
                            try:
                                if torch.sdaa.is_available():
                                    return "sdaa"
                            except Exception as e:
                                pass

        return "cpu"