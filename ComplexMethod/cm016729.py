def forward_timestep_embed(ts, x, emb, context=None, transformer_options={}, output_shape=None, time_context=None, num_video_frames=None, image_only_indicator=None):
    for layer in ts:
        if "patches" in transformer_options and "forward_timestep_embed_patch" in transformer_options["patches"]:
            found_patched = False
            for class_type, handler in transformer_options["patches"]["forward_timestep_embed_patch"]:
                if isinstance(layer, class_type):
                    x = handler(layer, x, emb, context, transformer_options, output_shape, time_context, num_video_frames, image_only_indicator)
                    found_patched = True
                    break
            if found_patched:
                continue

        if isinstance(layer, VideoResBlock):
            x = layer(x, emb, num_video_frames, image_only_indicator)
        elif isinstance(layer, TimestepBlock):
            x = layer(x, emb)
        elif isinstance(layer, SpatialVideoTransformer):
            x = layer(x, context, time_context, num_video_frames, image_only_indicator, transformer_options)
            if "transformer_index" in transformer_options:
                transformer_options["transformer_index"] += 1
        elif isinstance(layer, SpatialTransformer):
            x = layer(x, context, transformer_options)
            if "transformer_index" in transformer_options:
                transformer_options["transformer_index"] += 1
        elif isinstance(layer, Upsample):
            x = layer(x, output_shape=output_shape)
        else:
            x = layer(x)
    return x