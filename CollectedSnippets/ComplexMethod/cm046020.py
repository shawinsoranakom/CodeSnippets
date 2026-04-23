def atom_model_init(model_name: str, **kwargs):
    atom_model = None
    if model_name == AtomicModel.Layout:
        atom_model = pp_doclayout_v2_model_init(
            kwargs.get('pp_doclayout_v2_weights'),
            kwargs.get('device')
        )
    elif model_name == AtomicModel.MFR:
        atom_model = mfr_model_init(
            kwargs.get('mfr_weight_dir'),
            kwargs.get('device')
        )
    elif model_name == AtomicModel.OCR:
        atom_model = ocr_model_init(
            kwargs.get('det_db_box_thresh', 0.3),
            kwargs.get('lang'),
            kwargs.get('det_db_unclip_ratio', 1.8),
            kwargs.get('enable_merge_det_boxes', True)
        )
    elif model_name == AtomicModel.WirelessTable:
        atom_model = wireless_table_model_init(
            kwargs.get('lang'),
        )
    elif model_name == AtomicModel.WiredTable:
        atom_model = wired_table_model_init(
            kwargs.get('lang'),
        )
    elif model_name == AtomicModel.TableCls:
        atom_model = table_cls_model_init()
    elif model_name == AtomicModel.ImgOrientationCls:
        atom_model = img_orientation_cls_model_init()
    else:
        logger.error('model name not allow')
        exit(1)

    if atom_model is None:
        logger.error('model init failed')
        exit(1)
    else:
        return atom_model