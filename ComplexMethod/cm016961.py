async def execute(
        cls,
        image: Input.Image,
        image_left: Input.Image | None = None,
        image_back: Input.Image | None = None,
        image_right: Input.Image | None = None,
        model_version: str | None = None,
        orientation: str | None = None,
        texture: bool | None = None,
        pbr: bool | None = None,
        model_seed: int | None = None,
        texture_seed: int | None = None,
        texture_quality: str | None = None,
        geometry_quality: str | None = None,
        texture_alignment: str | None = None,
        face_limit: int | None = None,
        quad: bool | None = None,
    ) -> IO.NodeOutput:
        if image is None:
            raise RuntimeError("front image for multiview is required")
        images = []
        image_dict = {"image": image, "image_left": image_left, "image_back": image_back, "image_right": image_right}
        if image_left is None and image_back is None and image_right is None:
            raise RuntimeError("At least one of left, back, or right image must be provided for multiview")
        for image_name in ["image", "image_left", "image_back", "image_right"]:
            image_ = image_dict[image_name]
            if image_ is not None:
                images.append(
                    TripoFileReference(
                        root=TripoUrlReference(
                            url=(await upload_images_to_comfyapi(cls, image_, max_images=1))[0], type="jpeg"
                        )
                    )
                )
            else:
                images.append(TripoFileEmptyReference())
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/tripo/v2/openapi/task", method="POST"),
            response_model=TripoTaskResponse,
            data=TripoMultiviewToModelRequest(
                type=TripoTaskType.MULTIVIEW_TO_MODEL,
                files=images,
                model_version=model_version,
                orientation=orientation,
                texture=texture,
                pbr=pbr,
                model_seed=model_seed,
                texture_seed=texture_seed,
                texture_quality=texture_quality,
                geometry_quality=geometry_quality,
                texture_alignment=texture_alignment,
                face_limit=face_limit if face_limit != -1 else None,
                quad=quad,
            ),
        )
        return await poll_until_finished(cls, response, average_duration=80)