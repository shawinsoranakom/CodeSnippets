def benchmark(
    model=WEIGHTS_DIR / "yolo26n.pt",
    data=None,
    imgsz=160,
    half=False,
    int8=False,
    device="cpu",
    verbose=False,
    eps=1e-3,
    format="",
    **kwargs,
):
    """Benchmark a YOLO model across different formats for speed and accuracy.

    Args:
        model (str | Path): Path to the model file or directory.
        data (str | None): Dataset to evaluate on, inherited from TASK2DATA if not passed.
        imgsz (int): Image size for the benchmark.
        half (bool): Use half-precision for the model if True.
        int8 (bool): Use int8-precision for the model if True.
        device (str): Device to run the benchmark on, either 'cpu' or 'cuda'.
        verbose (bool | float): If True or a float, assert benchmarks pass with given metric.
        eps (float): Epsilon value for divide by zero prevention.
        format (str): Export format for benchmarking. If not supplied all formats are benchmarked.
        **kwargs (Any): Additional keyword arguments for exporter.

    Returns:
        (polars.DataFrame): A Polars DataFrame with benchmark results for each format, including file size, metric, and
            inference time.

    Examples:
        Benchmark a YOLO model with default settings:
        >>> from ultralytics.utils.benchmarks import benchmark
        >>> benchmark(model="yolo26n.pt", imgsz=640)
    """
    imgsz = check_imgsz(imgsz)
    assert imgsz[0] == imgsz[1] if isinstance(imgsz, list) else True, "benchmark() only supports square imgsz."

    import polars as pl  # scope for faster 'import ultralytics'

    pl.Config.set_tbl_cols(-1)  # Show all columns
    pl.Config.set_tbl_rows(-1)  # Show all rows
    pl.Config.set_tbl_width_chars(-1)  # No width limit
    pl.Config.set_tbl_hide_column_data_types(True)  # Hide data types
    pl.Config.set_tbl_hide_dataframe_shape(True)  # Hide shape info
    pl.Config.set_tbl_formatting("ASCII_BORDERS_ONLY_CONDENSED")

    device = select_device(device, verbose=False)
    if isinstance(model, (str, Path)):
        model = YOLO(model)
    data = data or TASK2DATA[model.task]  # task to dataset, i.e. coco8.yaml for task=detect
    key = TASK2METRIC[model.task]  # task to metric, i.e. metrics/mAP50-95(B) for task=detect

    y = []
    t0 = time.time()

    format_arg = format.lower()
    if format_arg:
        formats = frozenset(export_formats()["Argument"])
        assert format in formats, f"Expected format to be one of {formats}, but got '{format_arg}'."
    for name, format, suffix, cpu, gpu, _ in zip(*export_formats().values()):
        emoji, filename = "❌", None  # export defaults
        try:
            if format_arg and format_arg != format:
                continue

            # Checks
            if format == "pb":
                assert model.task != "obb", "TensorFlow GraphDef not supported for OBB task"
            elif format == "edgetpu":
                assert LINUX and not ARM64, "Edge TPU export only supported on non-aarch64 Linux"
            elif format == "tfjs":
                assert not (LINUX and ARM64), "TF.js export not supported on ARM64 Linux"
            elif format == "coreml":
                assert MACOS or (LINUX and not ARM64), "CoreML export only supported on macOS and non-aarch64 Linux"
            if format == "coreml":
                assert not IS_PYTHON_3_13, "CoreML not supported on Python 3.13"
            if format in {"saved_model", "pb", "tflite", "edgetpu", "tfjs"}:
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 TensorFlow exports not supported by onnx2tf yet"
                # assert not IS_PYTHON_MINIMUM_3_12, "TFLite exports not supported on Python>=3.12 yet"
            if format == "paddle":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 Paddle exports not supported yet"
                assert model.task != "obb", "Paddle OBB bug https://github.com/PaddlePaddle/Paddle/issues/72024"
                assert (LINUX and not IS_JETSON) or MACOS, "Windows and Jetson Paddle exports not supported yet"
            if format == "mnn":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 MNN exports not supported yet"
            if format == "ncnn":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 NCNN exports not supported yet"
            if format == "imx":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 IMX exports not supported"
                assert model.task in {"detect", "classify", "pose", "segment"}, (
                    "IMX export is only supported for detection, classification, pose estimation and segmentation tasks"
                )
                assert "C2f" in model.__str__(), "IMX only supported for YOLOv8n and YOLO11n"
            if format == "rknn":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 RKNN exports not supported yet"
                assert LINUX, "RKNN only supported on Linux"
                assert not is_rockchip(), "RKNN Inference only supported on Rockchip devices"
            if format == "executorch":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 ExecuTorch exports not supported yet"
            if format == "axelera":
                assert not isinstance(model, YOLOWorld), "YOLOWorldv2 Axelera exports not supported"
                assert LINUX and not (ARM64 and IS_DOCKER), (
                    "export is only supported on Linux and is not supported on ARM64 Docker."
                )
                assert not (model.task == "segment" and any(isinstance(m, Segment26) for m in model.model.modules())), (
                    "Axelera export does not currently support YOLO26 segmentation models"
                )
            if "cpu" in device.type:
                assert cpu, "inference not supported on CPU"
            if "cuda" in device.type:
                assert gpu, "inference not supported on GPU"

            # Export
            if format == "-":
                filename = model.pt_path or model.ckpt_path or model.model_name
                exported_model = deepcopy(model)  # PyTorch format
            else:
                filename = deepcopy(model).export(
                    imgsz=imgsz, format=format, half=half, int8=int8, data=data, device=device, verbose=False, **kwargs
                )
                exported_model = YOLO(filename, task=model.task)
                assert suffix in str(filename), "export failed"
            emoji = "❎"  # indicates export succeeded

            # Predict
            assert model.task != "pose" or format != "pb", "GraphDef Pose inference is not supported"
            assert format not in {"edgetpu", "tfjs"}, "inference not supported"
            assert format != "coreml" or platform.system() == "Darwin", "inference only supported on macOS>=10.13"
            assert format != "axelera", "inference only supported on Axelera hardware"
            exported_model.predict(ASSETS / "bus.jpg", imgsz=imgsz, device=device, half=half, verbose=False)

            # Validate
            results = exported_model.val(
                data=data,
                batch=1,
                imgsz=imgsz,
                plots=False,
                device=device,
                half=half,
                int8=int8,
                verbose=False,
                conf=0.001,  # all the pre-set benchmark mAP values are based on conf=0.001
            )
            metric, speed = results.results_dict[key], results.speed["inference"]
            fps = round(1000 / (speed + eps), 2)  # frames per second
            y.append([name, "✅", round(file_size(filename), 1), round(metric, 4), round(speed, 2), fps])
        except Exception as e:
            if verbose:
                assert type(e) is AssertionError, f"Benchmark failure for {name}: {e}"
            LOGGER.error(f"Benchmark failure for {name}: {e}")
            y.append([name, emoji, round(file_size(filename), 1), None, None, None])  # mAP, t_inference

    # Print results
    check_yolo(device=device)  # print system info
    df = pl.DataFrame(y, schema=["Format", "Status❔", "Size (MB)", key, "Inference time (ms/im)", "FPS"], orient="row")
    df = df.with_row_index(" ", offset=1)  # add index info
    df_display = df.with_columns(pl.all().cast(pl.String).fill_null("-"))

    name = model.model_name
    dt = time.time() - t0
    legend = "Benchmarks legend:  - ✅ Success  - ❎ Export passed but validation failed  - ❌️ Export failed"
    s = f"\nBenchmarks complete for {name} on {data} at imgsz={imgsz} ({dt:.2f}s)\n{legend}\n{df_display}\n"
    LOGGER.info(s)
    with open("benchmarks.log", "a", errors="ignore", encoding="utf-8") as f:
        f.write(s)

    if verbose and isinstance(verbose, float):
        metrics = df[key].to_numpy()  # values to compare to floor
        floor = verbose  # minimum metric floor to pass, i.e. = 0.29 mAP for YOLOv5n
        assert all(x > floor for x in metrics if not np.isnan(x)), f"Benchmark failure: metric(s) < floor {floor}"

    return df_display