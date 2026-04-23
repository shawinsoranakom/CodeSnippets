def __init__(
        self,
        image_encoder,
        memory_attention,
        memory_encoder,
        num_maskmem=7,
        image_size=512,
        backbone_stride=16,
        sigmoid_scale_for_mem_enc=1.0,
        sigmoid_bias_for_mem_enc=0.0,
        binarize_mask_from_pts_for_mem_enc=False,
        use_mask_input_as_output_without_sam=False,
        max_cond_frames_in_attn=-1,
        directly_add_no_mem_embed=False,
        use_high_res_features_in_sam=False,
        multimask_output_in_sam=False,
        multimask_min_pt_num=1,
        multimask_max_pt_num=1,
        multimask_output_for_tracking=False,
        use_multimask_token_for_obj_ptr: bool = False,
        iou_prediction_use_sigmoid=False,
        memory_temporal_stride_for_eval=1,
        non_overlap_masks_for_mem_enc=False,
        use_obj_ptrs_in_encoder=False,
        max_obj_ptrs_in_encoder=16,
        add_tpos_enc_to_obj_ptrs=True,
        proj_tpos_enc_in_obj_ptrs=False,
        use_signed_tpos_enc_to_obj_ptrs=False,
        only_obj_ptrs_in_the_past_for_eval=False,
        pred_obj_scores: bool = False,
        pred_obj_scores_mlp: bool = False,
        fixed_no_obj_ptr: bool = False,
        soft_no_obj_ptr: bool = False,
        use_mlp_for_obj_ptr_proj: bool = False,
        no_obj_embed_spatial: bool = False,
        sam_mask_decoder_extra_args=None,
        compile_image_encoder: bool = False,
    ):
        """Initialize the SAM2Model for video object segmentation with memory-based tracking.

        Args:
            image_encoder (nn.Module): Visual encoder for extracting image features.
            memory_attention (nn.Module): Module for attending to memory features.
            memory_encoder (nn.Module): Encoder for generating memory representations.
            num_maskmem (int): Number of accessible memory frames.
            image_size (int): Size of input images.
            backbone_stride (int): Stride of the image backbone output.
            sigmoid_scale_for_mem_enc (float): Scale factor for mask sigmoid probability.
            sigmoid_bias_for_mem_enc (float): Bias factor for mask sigmoid probability.
            binarize_mask_from_pts_for_mem_enc (bool): Whether to binarize sigmoid mask logits on interacted frames with
                clicks during evaluation.
            use_mask_input_as_output_without_sam (bool): Whether to directly output the input mask without using SAM
                prompt encoder and mask decoder on frames with mask input.
            max_cond_frames_in_attn (int): Maximum number of conditioning frames to participate in memory attention.
            directly_add_no_mem_embed (bool): Whether to directly add no-memory embedding to image feature on the first
                frame.
            use_high_res_features_in_sam (bool): Whether to use high-resolution feature maps in the SAM mask decoder.
            multimask_output_in_sam (bool): Whether to output multiple masks for the first click on initial conditioning
                frames.
            multimask_min_pt_num (int): Minimum number of clicks to use multimask output in SAM.
            multimask_max_pt_num (int): Maximum number of clicks to use multimask output in SAM.
            multimask_output_for_tracking (bool): Whether to use multimask output for tracking.
            use_multimask_token_for_obj_ptr (bool): Whether to use multimask tokens for object pointers.
            iou_prediction_use_sigmoid (bool): Whether to use sigmoid to restrict IoU prediction to [0-1].
            memory_temporal_stride_for_eval (int): Memory bank's temporal stride during evaluation.
            non_overlap_masks_for_mem_enc (bool): Whether to apply non-overlapping constraints on object masks in memory
                encoder during evaluation.
            use_obj_ptrs_in_encoder (bool): Whether to cross-attend to object pointers from other frames in the encoder.
            max_obj_ptrs_in_encoder (int): Maximum number of object pointers from other frames in encoder
                cross-attention.
            add_tpos_enc_to_obj_ptrs (bool): Whether to add temporal positional encoding to object pointers in the
                encoder.
            proj_tpos_enc_in_obj_ptrs (bool): Whether to add an extra linear projection layer for temporal positional
                encoding in object pointers.
            use_signed_tpos_enc_to_obj_ptrs (bool): Whether to use signed distance in the temporal positional encoding
                in the object pointers.
            only_obj_ptrs_in_the_past_for_eval (bool): Whether to only attend to object pointers in the past during
                evaluation.
            pred_obj_scores (bool): Whether to predict if there is an object in the frame.
            pred_obj_scores_mlp (bool): Whether to use an MLP to predict object scores.
            fixed_no_obj_ptr (bool): Whether to have a fixed no-object pointer when there is no object present.
            soft_no_obj_ptr (bool): Whether to mix in no-object pointer softly for easier recovery and error mitigation.
            use_mlp_for_obj_ptr_proj (bool): Whether to use MLP for object pointer projection.
            no_obj_embed_spatial (bool): Whether to add no-object embedding to spatial frames.
            sam_mask_decoder_extra_args (dict | None): Extra arguments for constructing the SAM mask decoder.
            compile_image_encoder (bool): Whether to compile the image encoder for faster inference.
        """
        super().__init__()

        # Part 1: the image backbone
        self.image_encoder = image_encoder
        # Use level 0, 1, 2 for high-res setting, or just level 2 for the default setting
        self.use_high_res_features_in_sam = use_high_res_features_in_sam
        self.num_feature_levels = 3 if use_high_res_features_in_sam else 1
        self.use_obj_ptrs_in_encoder = use_obj_ptrs_in_encoder
        self.max_obj_ptrs_in_encoder = max_obj_ptrs_in_encoder
        if use_obj_ptrs_in_encoder:
            # A conv layer to downsample the mask prompt to stride 4 (the same stride as
            # low-res SAM mask logits) and to change its scales from 0~1 to SAM logit scale,
            # so that it can be fed into the SAM mask decoder to generate a pointer.
            self.mask_downsample = torch.nn.Conv2d(1, 1, kernel_size=4, stride=4)
        self.add_tpos_enc_to_obj_ptrs = add_tpos_enc_to_obj_ptrs
        if proj_tpos_enc_in_obj_ptrs:
            assert add_tpos_enc_to_obj_ptrs  # these options need to be used together
        self.proj_tpos_enc_in_obj_ptrs = proj_tpos_enc_in_obj_ptrs
        self.use_signed_tpos_enc_to_obj_ptrs = use_signed_tpos_enc_to_obj_ptrs
        self.only_obj_ptrs_in_the_past_for_eval = only_obj_ptrs_in_the_past_for_eval

        # Part 2: memory attention to condition current frame's visual features
        # with memories (and obj ptrs) from past frames
        self.memory_attention = memory_attention
        self.hidden_dim = memory_attention.d_model

        # Part 3: memory encoder for the previous frame's outputs
        self.memory_encoder = memory_encoder
        self.mem_dim = self.hidden_dim
        if hasattr(self.memory_encoder, "out_proj") and hasattr(self.memory_encoder.out_proj, "weight"):
            # if there is compression of memories along channel dim
            self.mem_dim = self.memory_encoder.out_proj.weight.shape[0]
        self.num_maskmem = num_maskmem  # Number of memories accessible
        # Temporal encoding of the memories
        self.maskmem_tpos_enc = torch.nn.Parameter(torch.zeros(num_maskmem, 1, 1, self.mem_dim))
        trunc_normal_(self.maskmem_tpos_enc, std=0.02)
        # a single token to indicate no memory embedding from previous frames
        self.no_mem_embed = torch.nn.Parameter(torch.zeros(1, 1, self.hidden_dim))
        self.no_mem_pos_enc = torch.nn.Parameter(torch.zeros(1, 1, self.hidden_dim))
        trunc_normal_(self.no_mem_embed, std=0.02)
        trunc_normal_(self.no_mem_pos_enc, std=0.02)
        self.directly_add_no_mem_embed = directly_add_no_mem_embed
        # Apply sigmoid to the output raw mask logits (to turn them from
        # range (-inf, +inf) to range (0, 1)) before feeding them into the memory encoder
        self.sigmoid_scale_for_mem_enc = sigmoid_scale_for_mem_enc
        self.sigmoid_bias_for_mem_enc = sigmoid_bias_for_mem_enc
        self.binarize_mask_from_pts_for_mem_enc = binarize_mask_from_pts_for_mem_enc
        self.non_overlap_masks_for_mem_enc = non_overlap_masks_for_mem_enc
        self.memory_temporal_stride_for_eval = memory_temporal_stride_for_eval
        # On frames with mask input, whether to directly output the input mask without
        # using a SAM prompt encoder + mask decoder
        self.use_mask_input_as_output_without_sam = use_mask_input_as_output_without_sam
        self.multimask_output_in_sam = multimask_output_in_sam
        self.multimask_min_pt_num = multimask_min_pt_num
        self.multimask_max_pt_num = multimask_max_pt_num
        self.multimask_output_for_tracking = multimask_output_for_tracking
        self.use_multimask_token_for_obj_ptr = use_multimask_token_for_obj_ptr
        self.iou_prediction_use_sigmoid = iou_prediction_use_sigmoid

        # Part 4: SAM-style prompt encoder (for both mask and point inputs)
        # and SAM-style mask decoder for the final mask output
        self.image_size = image_size
        self.backbone_stride = backbone_stride
        self.sam_mask_decoder_extra_args = sam_mask_decoder_extra_args
        self.pred_obj_scores = pred_obj_scores
        self.pred_obj_scores_mlp = pred_obj_scores_mlp
        self.fixed_no_obj_ptr = fixed_no_obj_ptr
        self.soft_no_obj_ptr = soft_no_obj_ptr
        if self.fixed_no_obj_ptr:
            assert self.pred_obj_scores
            assert self.use_obj_ptrs_in_encoder
        if self.pred_obj_scores and self.use_obj_ptrs_in_encoder:
            self.no_obj_ptr = torch.nn.Parameter(torch.zeros(1, self.hidden_dim))
            trunc_normal_(self.no_obj_ptr, std=0.02)
        self.use_mlp_for_obj_ptr_proj = use_mlp_for_obj_ptr_proj
        self.no_obj_embed_spatial = None
        if no_obj_embed_spatial:
            self.no_obj_embed_spatial = torch.nn.Parameter(torch.zeros(1, self.mem_dim))
            trunc_normal_(self.no_obj_embed_spatial, std=0.02)

        self._build_sam_heads()
        self.max_cond_frames_in_attn = max_cond_frames_in_attn
        self.add_all_frames_to_correct_as_cond = True

        # Model compilation
        if compile_image_encoder:
            # Compile the forward function (not the full module) to allow loading checkpoints.
            LOGGER.info("Image encoder compilation is enabled. First forward pass will be slow.")
            self.image_encoder.forward = torch.compile(
                self.image_encoder.forward,
                mode="max-autotune",
                fullgraph=True,
                dynamic=False,
            )