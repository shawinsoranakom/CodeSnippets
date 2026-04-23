def wait_for_gpu_memory_to_clear(
    *,
    devices: list[int],
    threshold_bytes: int | None = None,
    threshold_ratio: float | None = None,
    timeout_s: float = 120,
) -> None:
    assert threshold_bytes is not None or threshold_ratio is not None
    # Use nvml instead of pytorch to reduce measurement error from torch cuda
    # context.
    devices = get_physical_device_indices(devices)
    start_time = time.time()
    while True:
        output: dict[int, str] = {}
        output_raw: dict[int, tuple[float, float]] = {}
        for device in devices:
            if current_platform.is_rocm():
                dev_handle = amdsmi_get_processor_handles()[device]
                mem_info = amdsmi_get_gpu_vram_usage(dev_handle)
                gb_used = mem_info["vram_used"] / 2**10
                gb_total = mem_info["vram_total"] / 2**10
            else:
                dev_handle = nvmlDeviceGetHandleByIndex(device)
                mem_info = nvmlDeviceGetMemoryInfo(dev_handle)
                gb_used = mem_info.used / 2**30
                gb_total = mem_info.total / 2**30
            output_raw[device] = (gb_used, gb_total)
            output[device] = f"{gb_used:.02f}/{gb_total:.02f}"

        print("gpu memory used/total (GiB): ", end="")
        for k, v in output.items():
            print(f"{k}={v}; ", end="")
        print("")

        if threshold_bytes is not None:
            is_free = lambda used, total: used <= threshold_bytes / 2**30
            threshold = f"{threshold_bytes / 2**30} GiB"
        else:
            is_free = lambda used, total: used / total <= threshold_ratio
            threshold = f"{threshold_ratio:.2f}"

        dur_s = time.time() - start_time
        if all(is_free(used, total) for used, total in output_raw.values()):
            print(
                f"Done waiting for free GPU memory on devices {devices=} "
                f"({threshold=}) {dur_s=:.02f}"
            )
            break

        if dur_s >= timeout_s:
            raise ValueError(
                f"Memory of devices {devices=} not free after "
                f"{dur_s=:.02f} ({threshold=})"
            )

        time.sleep(5)