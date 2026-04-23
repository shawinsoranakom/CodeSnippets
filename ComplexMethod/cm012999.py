def select_model_mode_for_export(model, mode: _C_onnx.TrainingMode):
    """A context manager to temporarily set the training mode of ``model``
    to ``mode``, resetting it when we exit the with-block.

    .. deprecated:: 2.7
        Please set training mode before exporting the model.

    Args:
        model: Same type and meaning as ``model`` arg to :func:`export`.
        mode: Same type and meaning as ``training`` arg to :func:`export`.
    """
    if not isinstance(mode, _C_onnx.TrainingMode):
        raise TypeError(
            f"'mode' should be a torch.onnx.TrainingMode enum, but got '{type(mode)}'."
        )
    originally_training: bool = False

    if hasattr(model, "training"):
        originally_training = model.training

        # ONNX opset 12 has better support for training amenable models, with updated
        # versions of the dropout and batch_norm operators
        if mode == _C_onnx.TrainingMode.TRAINING or (
            mode == _C_onnx.TrainingMode.PRESERVE and originally_training
        ):
            GLOBALS.export_training = True
            if GLOBALS.export_onnx_opset_version < 12:
                warnings.warn(
                    "You are exporting the model in training mode with onnx opset "
                    f"version {GLOBALS.export_onnx_opset_version}. "
                    "Opset versions lower than opset 12 will not be able to export "
                    "nodes such as Dropout and BatchNorm correctly.",
                    stacklevel=2,
                )
        else:
            GLOBALS.export_training = False

        GLOBALS.training_mode = mode
        if mode == _C_onnx.TrainingMode.TRAINING:
            model.train(True)
        elif mode == _C_onnx.TrainingMode.EVAL:
            model.train(False)
        # else mode == _C_onnx.TrainingMode.PRESERVE, do nothing

    try:
        yield
    finally:
        if hasattr(model, "training") and mode != _C_onnx.TrainingMode.PRESERVE:
            model.train(originally_training)