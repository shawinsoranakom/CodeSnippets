def model_info(model, detailed=False, verbose=True, imgsz=640):
    """Print and return detailed model information layer by layer.

    Args:
        model (nn.Module): Model to analyze.
        detailed (bool, optional): Whether to print detailed layer information.
        verbose (bool, optional): Whether to print model information.
        imgsz (int | list, optional): Input image size.

    Returns:
        (tuple): Tuple containing:
            - n_l (int): Number of layers.
            - n_p (int): Number of parameters.
            - n_g (int): Number of gradients.
            - flops (float): GFLOPs.
    """
    if not verbose:
        return
    n_p = get_num_params(model)  # number of parameters
    n_g = get_num_gradients(model)  # number of gradients
    layers = __import__("collections").OrderedDict((n, m) for n, m in model.named_modules() if len(m._modules) == 0)
    n_l = len(layers)  # number of layers
    if detailed:
        h = f"{'layer':>5}{'name':>40}{'type':>20}{'gradient':>10}{'parameters':>12}{'shape':>20}{'mu':>10}{'sigma':>10}"
        LOGGER.info(h)
        for i, (mn, m) in enumerate(layers.items()):
            mn = mn.replace("module_list.", "")
            mt = m.__class__.__name__
            if len(m._parameters):
                for pn, p in m.named_parameters():
                    LOGGER.info(
                        f"{i:>5g}{f'{mn}.{pn}':>40}{mt:>20}{p.requires_grad!r:>10}{p.numel():>12g}{list(p.shape)!s:>20}{p.mean():>10.3g}{p.std():>10.3g}{str(p.dtype).replace('torch.', ''):>15}"
                    )
            else:  # layers with no learnable params
                LOGGER.info(f"{i:>5g}{mn:>40}{mt:>20}{False!r:>10}{0:>12g}{[]!s:>20}{'-':>10}{'-':>10}{'-':>15}")

    flops = get_flops(model, imgsz)  # imgsz may be int or list, i.e. imgsz=640 or imgsz=[640, 320]
    fused = " (fused)" if getattr(model, "is_fused", lambda: False)() else ""
    fs = f", {flops:.1f} GFLOPs" if flops else ""
    yaml_file = getattr(model, "yaml_file", "") or getattr(model, "yaml", {}).get("yaml_file", "")
    model_name = Path(yaml_file).stem.replace("yolo", "YOLO") or "Model"
    LOGGER.info(f"{model_name} summary{fused}: {n_l:,} layers, {n_p:,} parameters, {n_g:,} gradients{fs}")
    return n_l, n_p, n_g, flops