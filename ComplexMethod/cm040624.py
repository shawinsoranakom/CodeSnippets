def make_layer_label(layer, **kwargs):
    class_name = layer.__class__.__name__

    show_layer_names = kwargs.pop("show_layer_names")
    show_layer_activations = kwargs.pop("show_layer_activations")
    show_dtype = kwargs.pop("show_dtype")
    show_shapes = kwargs.pop("show_shapes")
    show_trainable = kwargs.pop("show_trainable")
    if kwargs:
        raise ValueError(f"Invalid kwargs: {kwargs}")

    table = (
        '<<table border="0" cellborder="1" bgcolor="black" cellpadding="10">'
    )

    colspan_max = sum(int(x) for x in (show_dtype, show_trainable))
    if show_shapes:
        colspan_max += 2
    colspan = max(1, colspan_max)

    if show_layer_names:
        table += (
            f'<tr><td colspan="{colspan}" bgcolor="black">'
            '<font point-size="16" color="white">'
            f"<b>{layer.name}</b> ({class_name})"
            "</font></td></tr>"
        )
    else:
        table += (
            f'<tr><td colspan="{colspan}" bgcolor="black">'
            '<font point-size="16" color="white">'
            f"<b>{class_name}</b>"
            "</font></td></tr>"
        )
    if (
        show_layer_activations
        and hasattr(layer, "activation")
        and layer.activation is not None
    ):
        table += (
            f'<tr><td bgcolor="white" colspan="{colspan}">'
            '<font point-size="14">'
            f"Activation: <b>{get_layer_activation_name(layer)}</b>"
            "</font></td></tr>"
        )

    cols = []
    if show_shapes:
        input_shape = None
        output_shape = None
        try:
            input_shape = tree.map_structure(lambda x: x.shape, layer.input)
            output_shape = tree.map_structure(lambda x: x.shape, layer.output)
        except (ValueError, AttributeError):
            pass

        def format_shape(shape):
            if shape is not None:
                if isinstance(shape, dict):
                    shape_str = ", ".join(
                        [f"{k}: {v}" for k, v in shape.items()]
                    )
                else:
                    shape_str = f"{shape}"
                shape_str = shape_str.replace("}", "").replace("{", "")
            else:
                shape_str = "?"
            return shape_str

        if class_name != "InputLayer":
            cols.append(
                (
                    '<td bgcolor="white"><font point-size="14">'
                    f"Input shape: <b>{format_shape(input_shape)}</b>"
                    "</font></td>"
                )
            )
        cols.append(
            (
                '<td bgcolor="white"><font point-size="14">'
                f"Output shape: <b>{format_shape(output_shape)}</b>"
                "</font></td>"
            )
        )
    if show_dtype:
        dtype = None
        try:
            dtype = tree.map_structure(lambda x: x.dtype, layer.output)
        except (ValueError, AttributeError):
            pass
        cols.append(
            (
                '<td bgcolor="white"><font point-size="14">'
                f"Output dtype: <b>{dtype or '?'}</b>"
                "</font></td>"
            )
        )
    if show_trainable and hasattr(layer, "trainable") and layer.weights:
        if layer.trainable:
            cols.append(
                (
                    '<td bgcolor="forestgreen">'
                    '<font point-size="14" color="white">'
                    "<b>Trainable</b></font></td>"
                )
            )
        else:
            cols.append(
                (
                    '<td bgcolor="firebrick">'
                    '<font point-size="14" color="white">'
                    "<b>Non-trainable</b></font></td>"
                )
            )
    if cols:
        colspan = len(cols)
    else:
        colspan = 1

    if cols:
        table += f"<tr>{''.join(cols)}</tr>"
    table += "</table>>"
    return table