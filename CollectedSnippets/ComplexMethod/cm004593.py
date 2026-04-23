def forward(
        self,
        pixel_values: torch.FloatTensor | None = None,
        input_points: torch.FloatTensor | None = None,
        input_labels: torch.LongTensor | None = None,
        input_boxes: torch.FloatTensor | None = None,
        input_masks: torch.LongTensor | None = None,
        image_embeddings: torch.FloatTensor | None = None,
        multimask_output: bool = True,
        hq_token_only: bool = False,
        attention_similarity: torch.FloatTensor | None = None,
        target_embedding: torch.FloatTensor | None = None,
        intermediate_embeddings: list[torch.FloatTensor] | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> list[dict[str, torch.Tensor]]:
        r"""
        input_points (`torch.FloatTensor` of shape `(batch_size, num_points, 2)`):
            Input 2D spatial points, this is used by the prompt encoder to encode the prompt. Generally yields to much
            better results. The points can be obtained by passing a list of list of list to the processor that will
            create corresponding `torch` tensors of dimension 4. The first dimension is the image batch size, the
            second dimension is the point batch size (i.e. how many segmentation masks do we want the model to predict
            per input point), the third dimension is the number of points per segmentation mask (it is possible to pass
            multiple points for a single mask), and the last dimension is the x (vertical) and y (horizontal)
            coordinates of the point. If a different number of points is passed either for each image, or for each
            mask, the processor will create "PAD" points that will correspond to the (0, 0) coordinate, and the
            computation of the embedding will be skipped for these points using the labels.
        input_labels (`torch.LongTensor` of shape `(batch_size, point_batch_size, num_points)`):
            Input labels for the points, this is used by the prompt encoder to encode the prompt. According to the
            official implementation, there are 3 types of labels

            - `1`: the point is a point that contains the object of interest
            - `0`: the point is a point that does not contain the object of interest
            - `-1`: the point corresponds to the background

            We added the label:

            - `-10`: the point is a padding point, thus should be ignored by the prompt encoder

            The padding labels should be automatically done by the processor.
        input_boxes (`torch.FloatTensor` of shape `(batch_size, num_boxes, 4)`):
            Input boxes for the points, this is used by the prompt encoder to encode the prompt. Generally yields to
            much better generated masks. The boxes can be obtained by passing a list of list of list to the processor,
            that will generate a `torch` tensor, with each dimension corresponding respectively to the image batch
            size, the number of boxes per image and the coordinates of the top left and bottom right point of the box.
            In the order (`x1`, `y1`, `x2`, `y2`):

            - `x1`: the x coordinate of the top left point of the input box
            - `y1`: the y coordinate of the top left point of the input box
            - `x2`: the x coordinate of the bottom right point of the input box
            - `y2`: the y coordinate of the bottom right point of the input box
        input_masks (`torch.FloatTensor` of shape `(batch_size, image_size, image_size)`):
            SAM_HQ model also accepts segmentation masks as input. The mask will be embedded by the prompt encoder to
            generate a corresponding embedding, that will be fed later on to the mask decoder. These masks needs to be
            manually fed by the user, and they need to be of shape (`batch_size`, `image_size`, `image_size`).
        image_embeddings (`torch.FloatTensor` of shape `(batch_size, output_channels, window_size, window_size)`):
            Image embeddings, this is used by the mask decder to generate masks and iou scores. For more memory
            efficient computation, users can first retrieve the image embeddings using the `get_image_embeddings`
            method, and then feed them to the `forward` method instead of feeding the `pixel_values`.
        multimask_output (`bool`, *optional*):
            In the original implementation and paper, the model always outputs 3 masks per image (or per point / per
            bounding box if relevant). However, it is possible to just output a single mask, that corresponds to the
            "best" mask, by specifying `multimask_output=False`.
        hq_token_only (`bool`, *optional*, defaults to `False`):
            Whether to use only the HQ token path for mask generation. When False, combines both standard and HQ paths.
            This is specific to SAM-HQ's architecture.
        attention_similarity (`torch.FloatTensor`, *optional*):
            Attention similarity tensor, to be provided to the mask decoder for target-guided attention in case the
            model is used for personalization as introduced in [PerSAM](https://huggingface.co/papers/2305.03048).
        target_embedding (`torch.FloatTensor`, *optional*):
            Embedding of the target concept, to be provided to the mask decoder for target-semantic prompting in case
            the model is used for personalization as introduced in [PerSAM](https://huggingface.co/papers/2305.03048).
        intermediate_embeddings (`List[torch.FloatTensor]`, *optional*):
            Intermediate embeddings from vision encoder's non-windowed blocks, used by SAM-HQ for enhanced mask quality.
            Required when providing pre-computed image_embeddings instead of pixel_values.

        Example:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoModel, AutoProcessor

        >>> model = AutoModel.from_pretrained("sushmanth/sam_hq_vit_b")
        >>> processor = AutoProcessor.from_pretrained("sushmanth/sam_hq_vit_b")

        >>> url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/sam-car.png"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read())).convert("RGB")
        >>> input_points = [[[400, 650]]]  # 2D location of a window on the car
        >>> inputs = processor(images=image, input_points=input_points, return_tensors="pt")

        >>> # Get high-quality segmentation mask
        >>> outputs = model(**inputs)

        >>> # For high-quality mask only
        >>> outputs = model(**inputs, hq_token_only=True)

        >>> # Postprocess masks
        >>> masks = processor.post_process_masks(
        ...     outputs.pred_masks, inputs["original_sizes"], inputs["reshaped_input_sizes"]
        ... )
        ```
        """
        if pixel_values is None and image_embeddings is None:
            raise ValueError("Either pixel_values or image_embeddings must be provided.")

        if pixel_values is not None and image_embeddings is not None:
            raise ValueError("Only one of pixel_values and image_embeddings can be provided.")

        if input_points is not None and len(input_points.shape) != 4:
            raise ValueError(
                "The input_points must be a 4D tensor. Of shape `batch_size`, `point_batch_size`, `nb_points_per_image`, `2`."
                f" got {input_points.shape}."
            )

        if input_boxes is not None and len(input_boxes.shape) != 3:
            raise ValueError(
                "The input_boxes must be a 3D tensor. Of shape `batch_size`, `nb_boxes`, `4`."
                f" got {input_boxes.shape}."
            )

        # Add validation for point and box batch sizes
        if input_points is not None and input_boxes is not None:
            point_batch_size = input_points.shape[1]
            box_batch_size = input_boxes.shape[1]
            if point_batch_size != box_batch_size:
                raise ValueError(
                    f"You should provide as many bounding boxes as input points per box. Got {point_batch_size} and {box_batch_size}."
                )

        image_positional_embeddings = self.get_image_wide_positional_embeddings()
        # repeat with batch size
        batch_size = pixel_values.shape[0] if pixel_values is not None else image_embeddings.shape[0]
        image_positional_embeddings = image_positional_embeddings.repeat(batch_size, 1, 1, 1)

        if pixel_values is not None:
            vision_outputs = self.vision_encoder(pixel_values, **kwargs)
            image_embeddings = vision_outputs.last_hidden_state
            intermediate_embeddings = vision_outputs.intermediate_embeddings
        if input_points is not None and input_labels is None:
            input_labels = torch.ones_like(input_points[:, :, :, 0], dtype=torch.int, device=input_points.device)

        sparse_embeddings, dense_embeddings = self.prompt_encoder(
            input_points=input_points,
            input_labels=input_labels,
            input_boxes=input_boxes,
            input_masks=input_masks,
        )

        # Predict masks
        mask_decoder_output = self.mask_decoder(
            image_embeddings=image_embeddings,
            image_positional_embeddings=image_positional_embeddings,
            sparse_prompt_embeddings=sparse_embeddings,
            dense_prompt_embeddings=dense_embeddings,
            multimask_output=multimask_output,
            hq_token_only=hq_token_only,
            intermediate_embeddings=intermediate_embeddings,
            attention_similarity=attention_similarity,
            target_embedding=target_embedding,
        )
        return SamHQImageSegmentationOutput(
            iou_scores=mask_decoder_output[1],
            pred_masks=mask_decoder_output[0],
            vision_hidden_states=vision_outputs.hidden_states if pixel_values is not None else None,
            vision_attentions=vision_outputs.attentions if pixel_values is not None else None,
        )