def clean_memory(device='cuda'):
    if str(device).startswith("cuda"):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    elif str(device).startswith("npu"):
        if torch_npu.npu.is_available():
            torch_npu.npu.empty_cache()
    elif str(device).startswith("mps"):
        torch.mps.empty_cache()
    elif str(device).startswith("gcu"):
        if torch.gcu.is_available():
            torch.gcu.empty_cache()
    elif str(device).startswith("musa"):
        if torch.musa.is_available():
            torch.musa.empty_cache()
    elif str(device).startswith("mlu"):
        if torch.mlu.is_available():
            torch.mlu.empty_cache()
    elif str(device).startswith("sdaa"):
        if torch.sdaa.is_available():
            torch.sdaa.empty_cache()  
    gc.collect()