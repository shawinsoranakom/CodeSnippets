def load_t2i_adapter(t2i_data, model_options={}): #TODO: model_options
    compression_ratio = 8
    upscale_algorithm = 'nearest-exact'

    if 'adapter' in t2i_data:
        t2i_data = t2i_data['adapter']
    if 'adapter.body.0.resnets.0.block1.weight' in t2i_data: #diffusers format
        prefix_replace = {}
        for i in range(4):
            for j in range(2):
                prefix_replace["adapter.body.{}.resnets.{}.".format(i, j)] = "body.{}.".format(i * 2 + j)
            prefix_replace["adapter.body.{}.".format(i, )] = "body.{}.".format(i * 2)
        prefix_replace["adapter."] = ""
        t2i_data = comfy.utils.state_dict_prefix_replace(t2i_data, prefix_replace)
    keys = t2i_data.keys()

    if "body.0.in_conv.weight" in keys:
        cin = t2i_data['body.0.in_conv.weight'].shape[1]
        model_ad = comfy.t2i_adapter.adapter.Adapter_light(cin=cin, channels=[320, 640, 1280, 1280], nums_rb=4)
    elif 'conv_in.weight' in keys:
        cin = t2i_data['conv_in.weight'].shape[1]
        channel = t2i_data['conv_in.weight'].shape[0]
        ksize = t2i_data['body.0.block2.weight'].shape[2]
        use_conv = False
        down_opts = list(filter(lambda a: a.endswith("down_opt.op.weight"), keys))
        if len(down_opts) > 0:
            use_conv = True
        xl = False
        if cin == 256 or cin == 768:
            xl = True
        model_ad = comfy.t2i_adapter.adapter.Adapter(cin=cin, channels=[channel, channel*2, channel*4, channel*4][:4], nums_rb=2, ksize=ksize, sk=True, use_conv=use_conv, xl=xl)
    elif "backbone.0.0.weight" in keys:
        model_ad = comfy.ldm.cascade.controlnet.ControlNet(c_in=t2i_data['backbone.0.0.weight'].shape[1], proj_blocks=[0, 4, 8, 12, 51, 55, 59, 63])
        compression_ratio = 32
        upscale_algorithm = 'bilinear'
    elif "backbone.10.blocks.0.weight" in keys:
        model_ad = comfy.ldm.cascade.controlnet.ControlNet(c_in=t2i_data['backbone.0.weight'].shape[1], bottleneck_mode="large", proj_blocks=[0, 4, 8, 12, 51, 55, 59, 63])
        compression_ratio = 1
        upscale_algorithm = 'nearest-exact'
    else:
        return None

    missing, unexpected = model_ad.load_state_dict(t2i_data)
    if len(missing) > 0:
        logging.warning("t2i missing {}".format(missing))

    if len(unexpected) > 0:
        logging.debug("t2i unexpected {}".format(unexpected))

    return T2IAdapter(model_ad, model_ad.input_channels, compression_ratio, upscale_algorithm)