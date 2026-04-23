def load_pretrained_params(model, path):
    logger = get_logger()
    path = maybe_download_params(path)
    if path.endswith(".pdparams"):
        path = path.replace(".pdparams", "")
    assert os.path.exists(
        path + ".pdparams"
    ), "The {}.pdparams does not exists!".format(path)

    params = paddle.load(path + ".pdparams")

    state_dict = model.state_dict()

    new_state_dict = {}
    is_float16 = False

    for k1 in params.keys():
        if k1 not in state_dict.keys():
            logger.warning("The pretrained params {} not in model".format(k1))
        else:
            if params[k1].dtype == paddle.float16:
                is_float16 = True
            if params[k1].dtype != state_dict[k1].dtype:
                params[k1] = params[k1].astype(state_dict[k1].dtype)
            if list(state_dict[k1].shape) == list(params[k1].shape):
                new_state_dict[k1] = params[k1]
            else:
                logger.warning(
                    "The shape of model params {} {} not matched with loaded params {} {} !".format(
                        k1, state_dict[k1].shape, k1, params[k1].shape
                    )
                )

    model.set_state_dict(new_state_dict)
    if is_float16:
        logger.info(
            "The parameter type is float16, which is converted to float32 when loading"
        )
    logger.info("load pretrain successful from {}".format(path))
    return is_float16