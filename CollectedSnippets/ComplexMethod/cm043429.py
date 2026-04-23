def export_saved_model(
    model,
    im,
    file,
    dynamic,
    tf_nms=False,
    agnostic_nms=False,
    topk_per_class=100,
    topk_all=100,
    iou_thres=0.45,
    conf_thres=0.25,
    keras=False,
    prefix=colorstr("TensorFlow SavedModel:"),
):
    """Export a YOLOv5 model to the TensorFlow SavedModel format, supporting dynamic axes and non-maximum suppression
    (NMS).

    Args:
        model (torch.nn.Module): The PyTorch model to convert.
        im (torch.Tensor): Sample input tensor with shape (B, C, H, W) for tracing.
        file (pathlib.Path): File path to save the exported model.
        dynamic (bool): Flag to indicate whether dynamic axes should be used.
        tf_nms (bool, optional): Enable TensorFlow non-maximum suppression (NMS). Default is False.
        agnostic_nms (bool, optional): Enable class-agnostic NMS. Default is False.
        topk_per_class (int, optional): Top K detections per class to keep before applying NMS. Default is 100.
        topk_all (int, optional): Top K detections across all classes to keep before applying NMS. Default is 100.
        iou_thres (float, optional): IoU threshold for NMS. Default is 0.45.
        conf_thres (float, optional): Confidence threshold for detections. Default is 0.25.
        keras (bool, optional): Save the model in Keras format if True. Default is False.
        prefix (str, optional): Prefix for logging messages. Default is "TensorFlow SavedModel:".

    Returns:
        tuple[str, tf.keras.Model | None]: A tuple containing the path to the saved model folder and the Keras model instance,
        or None if TensorFlow export fails.

    Examples:
        ```python
        model, im = ...  # Initialize your PyTorch model and input tensor
        export_saved_model(model, im, Path("yolov5_saved_model"), dynamic=True)
        ```

    Notes:
        - The method supports TensorFlow versions up to 2.15.1.
        - TensorFlow NMS may not be supported in older TensorFlow versions.
        - If the TensorFlow version exceeds 2.13.1, it might cause issues when exporting to TFLite.
          Refer to: https://github.com/ultralytics/yolov5/issues/12489
    """
    # YOLOv5 TensorFlow SavedModel export
    try:
        import tensorflow as tf
    except Exception:
        check_requirements(f"tensorflow{'' if torch.cuda.is_available() else '-macos' if MACOS else '-cpu'}<=2.15.1")

        import tensorflow as tf
    from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2

    from models.tf import TFModel

    LOGGER.info(f"\n{prefix} starting export with tensorflow {tf.__version__}...")
    if tf.__version__ > "2.13.1":
        helper_url = "https://github.com/ultralytics/yolov5/issues/12489"
        LOGGER.info(
            f"WARNING ⚠️ using Tensorflow {tf.__version__} > 2.13.1 might cause issue when exporting the model to tflite {helper_url}"
        )  # handling issue https://github.com/ultralytics/yolov5/issues/12489
    f = str(file).replace(".pt", "_saved_model")
    batch_size, ch, *imgsz = list(im.shape)  # BCHW

    tf_model = TFModel(cfg=model.yaml, model=model, nc=model.nc, imgsz=imgsz)
    im = tf.zeros((batch_size, *imgsz, ch))  # BHWC order for TensorFlow
    _ = tf_model.predict(im, tf_nms, agnostic_nms, topk_per_class, topk_all, iou_thres, conf_thres)
    inputs = tf.keras.Input(shape=(*imgsz, ch), batch_size=None if dynamic else batch_size)
    outputs = tf_model.predict(inputs, tf_nms, agnostic_nms, topk_per_class, topk_all, iou_thres, conf_thres)
    keras_model = tf.keras.Model(inputs=inputs, outputs=outputs)
    keras_model.trainable = False
    keras_model.summary()
    if keras:
        keras_model.save(f, save_format="tf")
    else:
        spec = tf.TensorSpec(keras_model.inputs[0].shape, keras_model.inputs[0].dtype)
        m = tf.function(lambda x: keras_model(x))  # full model
        m = m.get_concrete_function(spec)
        frozen_func = convert_variables_to_constants_v2(m)
        tfm = tf.Module()
        tfm.__call__ = tf.function(lambda x: frozen_func(x)[:4] if tf_nms else frozen_func(x), [spec])
        tfm.__call__(im)
        tf.saved_model.save(
            tfm,
            f,
            options=tf.saved_model.SaveOptions(experimental_custom_gradients=False)
            if check_version(tf.__version__, "2.6")
            else tf.saved_model.SaveOptions(),
        )
    return f, keras_model