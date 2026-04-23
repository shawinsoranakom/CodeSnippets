def __init__(
            self,
            device=None,
            lang=None,
            formula_enable=True,
    ):
        if device is not None:
            self.device = device
        else:
            self.device = get_device()

        self.lang = lang

        self.enable_ocr_det_batch = ocr_det_batch_setting()

        if str(self.device).startswith('npu'):
            try:
                import torch_npu
                if torch_npu.npu.is_available():
                    torch_npu.npu.set_compile_mode(jit_compile=False)
            except Exception as e:
                raise RuntimeError(
                    "NPU is selected as device, but torch_npu is not available. "
                    "Please ensure that the torch_npu package is installed correctly."
                ) from e

        self.atom_model_manager = AtomModelSingleton()

        # 初始化OCR模型
        self.ocr_model = self.atom_model_manager.get_atom_model(
            atom_model_name=AtomicModel.OCR,
            det_db_box_thresh=0.3,
            lang=self.lang
        )

        if formula_enable:
            # 初始化layout模型，用于提供行内公式检测框
            self.layout_model = self.atom_model_manager.get_atom_model(
                atom_model_name=AtomicModel.Layout,
                pp_doclayout_v2_weights=str(
                    os.path.join(
                        auto_download_and_get_model_root_path(ModelPath.pp_doclayout_v2),
                        ModelPath.pp_doclayout_v2,
                    )
                ),
                device=self.device,
            )

            # 初始化公式解析模型
            if MFR_MODEL == "unimernet_small":
                mfr_model_path = ModelPath.unimernet_small
            elif MFR_MODEL == "pp_formulanet_plus_m":
                mfr_model_path = ModelPath.pp_formulanet_plus_m
            else:
                logger.error('MFR model name not allow')
                exit(1)

            self.mfr_model = self.atom_model_manager.get_atom_model(
                atom_model_name=AtomicModel.MFR,
                mfr_weight_dir=str(os.path.join(auto_download_and_get_model_root_path(mfr_model_path), mfr_model_path)),
                device=self.device,
            )