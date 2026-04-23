def serialize_item(cls, obj: object) -> Iterable[bytes | memoryview]:
        # Simple cases
        if isinstance(obj, (bytes, memoryview)):
            return (obj,)
        if isinstance(obj, str):
            return (obj.encode("utf-8"),)
        if isinstance(obj, (int, float)):
            return (np.array(obj).tobytes(),)

        if isinstance(obj, Image.Image):
            exif = obj.getexif()
            if Image.ExifTags.Base.ImageID in exif and isinstance(
                exif[Image.ExifTags.Base.ImageID], uuid.UUID
            ):
                return (exif[Image.ExifTags.Base.ImageID].bytes,)

            data = {"mode": obj.mode, "data": np.asarray(obj)}
            palette = obj.palette
            if palette is not None:
                data["palette"] = palette.palette
                if palette.rawmode is not None:
                    data["palette_rawmode"] = palette.rawmode

            return cls.iter_item_to_bytes("image", data)

        if isinstance(obj, MediaWithBytes) and isinstance(obj.media, Image.Image):
            exif = obj.media.getexif()
            if Image.ExifTags.Base.ImageID in exif and isinstance(
                exif[Image.ExifTags.Base.ImageID], uuid.UUID
            ):
                return (exif[Image.ExifTags.Base.ImageID].bytes,)

            return cls.iter_item_to_bytes("image", obj.original_bytes)

        if isinstance(obj, torch.Tensor):
            tensor_obj: torch.Tensor = obj.cpu()
            tensor_dtype = tensor_obj.dtype
            tensor_shape = tensor_obj.shape

            # NumPy does not support bfloat16.
            # Workaround: View the tensor as a contiguous 1D array of bytes
            if tensor_dtype == torch.bfloat16:
                tensor_obj = tensor_obj.contiguous()
                tensor_obj = tensor_obj.view((tensor_obj.numel(),)).view(torch.uint8)

                return cls.iter_item_to_bytes(
                    "tensor",
                    {
                        "original_dtype": str(tensor_dtype),
                        "original_shape": tuple(tensor_shape),
                        "data": tensor_obj.numpy(),
                    },
                )

            return cls.iter_item_to_bytes("tensor", tensor_obj.numpy())

        if isinstance(obj, np.ndarray):
            if obj.ndim == 0:
                arr_data = obj.item()
            elif obj.flags.c_contiguous:
                # Not valid for 0-D arrays
                arr_data = obj.view(np.uint8).data
            else:
                # If the array is non-contiguous, we need to copy it first
                arr_data = obj.tobytes()

            return cls.iter_item_to_bytes(
                "ndarray",
                {
                    "dtype": obj.dtype.str,
                    "shape": obj.shape,
                    "data": arr_data,
                },
            )

        logger.warning(
            "No serialization method found for %s. Falling back to pickle.", type(obj)
        )

        return (pickle.dumps(obj),)