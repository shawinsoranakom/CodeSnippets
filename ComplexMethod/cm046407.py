def onnx2saved_model(
    onnx_file: str,
    output_dir: Path | str,
    int8: bool = False,
    images: np.ndarray | None = None,
    disable_group_convolution: bool = False,
    prefix: str = "",
):
    """Convert an ONNX model to TensorFlow SavedModel format using onnx2tf.

    Args:
        onnx_file (str): ONNX file path.
        output_dir (Path | str): Output directory path for the SavedModel.
        int8 (bool, optional): Enable INT8 quantization. Defaults to False.
        images (np.ndarray | None, optional): Calibration images for INT8 quantization in BHWC format.
        disable_group_convolution (bool, optional): Disable group convolution optimization. Defaults to False.
        prefix (str, optional): Logging prefix. Defaults to "".

    Returns:
        (keras.Model): Converted Keras model.

    Notes:
        - Requires onnx2tf package. Downloads calibration data if INT8 quantization is enabled.
        - Removes temporary files and renames quantized models after conversion.
    """
    output_dir = Path(output_dir)
    # Pre-download calibration file to fix https://github.com/PINTO0309/onnx2tf/issues/545
    onnx2tf_file = Path("calibration_image_sample_data_20x128x128x3_float32.npy")
    if not onnx2tf_file.exists():
        attempt_download_asset(f"{onnx2tf_file}.zip", unzip=True, delete=True)
    np_data = None
    if int8:
        tmp_file = output_dir / "tmp_tflite_int8_calibration_images.npy"  # int8 calibration images file
        if images is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            np.save(str(tmp_file), images)  # BHWC
            np_data = [["images", tmp_file, [[[[0, 0, 0]]]], [[[[255, 255, 255]]]]]]

    # Patch onnx.helper for onnx_graphsurgeon compatibility with ONNX>=1.17
    # The float32_to_bfloat16 function was removed in ONNX 1.17, but onnx_graphsurgeon still uses it
    import onnx.helper

    if not hasattr(onnx.helper, "float32_to_bfloat16"):
        import struct

        def float32_to_bfloat16(fval):
            """Convert float32 to bfloat16 (truncates lower 16 bits of mantissa)."""
            ival = struct.unpack("=I", struct.pack("=f", fval))[0]
            return ival >> 16

        onnx.helper.float32_to_bfloat16 = float32_to_bfloat16

    import onnx2tf  # scoped for after ONNX export for reduced conflict during import

    LOGGER.info(f"{prefix} starting TFLite export with onnx2tf {onnx2tf.__version__}...")
    keras_model = onnx2tf.convert(
        input_onnx_file_path=onnx_file,
        output_folder_path=str(output_dir),
        not_use_onnxsim=True,
        verbosity="error",  # note INT8-FP16 activation bug https://github.com/ultralytics/ultralytics/issues/15873
        output_integer_quantized_tflite=int8,
        custom_input_op_name_np_data_path=np_data,
        enable_batchmatmul_unfold=not int8,  # fix lower no. of detected objects on GPU delegate
        output_signaturedefs=True,  # fix error with Attention block group convolution
        disable_group_convolution=disable_group_convolution,  # fix error with group convolution
    )

    # Remove/rename TFLite models
    if int8:
        tmp_file.unlink(missing_ok=True)
        for file in output_dir.rglob("*_dynamic_range_quant.tflite"):
            file.rename(file.with_name(file.stem.replace("_dynamic_range_quant", "_int8") + file.suffix))
        for file in output_dir.rglob("*_integer_quant_with_int16_act.tflite"):
            file.unlink()  # delete extra fp16 activation TFLite files
    return keras_model