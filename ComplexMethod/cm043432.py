def _create(name, pretrained=True, channels=3, classes=80, autoshape=True, verbose=True, device=None):
    """Creates or loads a YOLOv5 model, with options for pretrained weights and model customization.

    Args:
        name (str): Model name (e.g., 'yolov5s') or path to the model checkpoint (e.g., 'path/to/best.pt').
        pretrained (bool, optional): If True, loads pretrained weights into the model. Defaults to True.
        channels (int, optional): Number of input channels the model expects. Defaults to 3.
        classes (int, optional): Number of classes the model is expected to detect. Defaults to 80.
        autoshape (bool, optional): If True, applies the YOLOv5 .autoshape() wrapper for various input formats. Defaults
            to True.
        verbose (bool, optional): If True, prints detailed information during the model creation/loading process.
            Defaults to True.
        device (str | torch.device | None, optional): Device to use for model parameters (e.g., 'cpu', 'cuda'). If None,
            selects the best available device. Defaults to None.

    Returns:
        (DetectMultiBackend | AutoShape): The loaded YOLOv5 model, potentially wrapped with AutoShape if specified.

    Examples:
        ```python
        import torch
        from ultralytics import _create

        # Load an official YOLOv5s model with pretrained weights
        model = _create('yolov5s')

        # Load a custom model from a local checkpoint
        model = _create('path/to/custom_model.pt', pretrained=False)

        # Load a model with specific input channels and classes
        model = _create('yolov5s', channels=1, classes=10)
        ```

    Notes:
        For more information on model loading and customization, visit the
        [YOLOv5 PyTorch Hub Documentation](https://docs.ultralytics.com/yolov5/tutorials/pytorch_hub_model_loading/).
    """
    from pathlib import Path

    from models.common import AutoShape, DetectMultiBackend
    from models.experimental import attempt_load
    from models.yolo import ClassificationModel, DetectionModel, SegmentationModel
    from utils.downloads import attempt_download
    from utils.general import LOGGER, ROOT, check_requirements, intersect_dicts, logging
    from utils.torch_utils import select_device

    if not verbose:
        LOGGER.setLevel(logging.WARNING)
    check_requirements(ROOT / "requirements.txt", exclude=("opencv-python", "tensorboard", "thop"))
    name = Path(name)
    path = name.with_suffix(".pt") if name.suffix == "" and not name.is_dir() else name  # checkpoint path
    try:
        device = select_device(device)
        if pretrained and channels == 3 and classes == 80:
            try:
                model = DetectMultiBackend(path, device=device, fuse=autoshape)  # detection model
                if autoshape:
                    if model.pt and isinstance(model.model, ClassificationModel):
                        LOGGER.warning(
                            "WARNING ⚠️ YOLOv5 ClassificationModel is not yet AutoShape compatible. "
                            "You must pass torch tensors in BCHW to this model, i.e. shape(1,3,224,224)."
                        )
                    elif model.pt and isinstance(model.model, SegmentationModel):
                        LOGGER.warning(
                            "WARNING ⚠️ YOLOv5 SegmentationModel is not yet AutoShape compatible. "
                            "You will not be able to run inference with this model."
                        )
                    else:
                        model = AutoShape(model)  # for file/URI/PIL/cv2/np inputs and NMS
            except Exception:
                model = attempt_load(path, device=device, fuse=False)  # arbitrary model
        else:
            cfg = next(iter((Path(__file__).parent / "models").rglob(f"{path.stem}.yaml")))  # model.yaml path
            model = DetectionModel(cfg, channels, classes)  # create model
            if pretrained:
                ckpt = torch_load(attempt_download(path), map_location=device)  # load
                csd = ckpt["model"].float().state_dict()  # checkpoint state_dict as FP32
                csd = intersect_dicts(csd, model.state_dict(), exclude=["anchors"])  # intersect
                model.load_state_dict(csd, strict=False)  # load
                if len(ckpt["model"].names) == classes:
                    model.names = ckpt["model"].names  # set class names attribute
        if not verbose:
            LOGGER.setLevel(logging.INFO)  # reset to default
        return model.to(device)

    except Exception as e:
        help_url = "https://docs.ultralytics.com/yolov5/tutorials/pytorch_hub_model_loading"
        s = f"{e}. Cache may be out of date, try `force_reload=True` or see {help_url} for help."
        raise Exception(s) from e