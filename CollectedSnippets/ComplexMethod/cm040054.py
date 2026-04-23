def convert_format(
        self,
        boxes,
        source,
        target,
        height=None,
        width=None,
        dtype="float32",
    ):
        if isinstance(boxes, dict):
            boxes["boxes"] = self.convert_format(
                boxes["boxes"],
                source=source,
                target=target,
                height=height,
                width=width,
                dtype=dtype,
            )
            return boxes

        to_xyxy_converters = {
            "xyxy": self._xyxy_to_xyxy,
            "yxyx": self._yxyx_to_xyxy,
            "xywh": self._xywh_to_xyxy,
            "center_xywh": self._center_xywh_to_xyxy,
            "center_yxhw": self._center_yxhw_to_xyxy,
            "rel_xyxy": self._rel_xyxy_to_xyxy,
            "rel_yxyx": self._rel_yxyx_to_xyxy,
            "rel_xywh": self._rel_xywh_to_xyxy,
            "rel_center_xywh": self._rel_center_xywh_to_xyxy,
        }
        from_xyxy_converters = {
            "xyxy": self._xyxy_to_xyxy,
            "yxyx": self._xyxy_to_yxyx,
            "xywh": self._xyxy_to_xywh,
            "center_xywh": self._xyxy_to_center_xywh,
            "center_yxhw": self._xyxy_to_center_yxhw,
            "rel_xyxy": self._xyxy_to_rel_xyxy,
            "rel_yxyx": self._xyxy_to_rel_yxyx,
            "rel_xywh": self._xyxy_to_rel_xywh,
            "rel_center_xywh": self._xyxy_to_rel_center_xywh,
        }

        ops = self.backend
        boxes_shape = ops.shape(boxes)
        if boxes_shape[-1] != 4:
            raise ValueError(
                "`boxes` must be a tensor with the last dimension of 4. "
                f"Received: boxes.shape={boxes_shape}"
            )
        source = source.lower()
        target = target.lower()
        if source not in SUPPORTED_FORMATS or target not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Invalid source or target format. "
                f"Supported formats: {SUPPORTED_FORMATS}"
            )

        if (source.startswith("rel_") or target.startswith("rel_")) and (
            width is None or height is None
        ):
            raise ValueError(
                "convert_format() must receive `height` and `width` "
                "transforming between relative and absolute formats."
                f"convert_format() received source=`{source}`, "
                f"target=`{target}, "
                f"but height={height} and width={width}."
            )
        boxes = ops.cast(boxes, dtype)
        if source == target:
            return boxes
        if width is not None:
            width = ops.cast(width, dtype)
        if height is not None:
            height = ops.cast(height, dtype)

        if source.startswith("rel_") and target.startswith("rel_"):
            source = source.replace("rel_", "", 1)
            target = target.replace("rel_", "", 1)
        to_xyxy_converter = to_xyxy_converters[source]
        from_xyxy_converter = from_xyxy_converters[target]
        in_xyxy_boxes = to_xyxy_converter(boxes, height, width)
        return from_xyxy_converter(in_xyxy_boxes, height, width)