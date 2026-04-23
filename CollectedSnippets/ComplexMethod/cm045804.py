def _group_shape_transform(shape) -> _SlideTransform:
        group_properties = getattr(shape._element, "grpSpPr", None)
        xfrm = (
            getattr(group_properties, "xfrm", None)
            if group_properties is not None
            else None
        )
        if xfrm is None:
            return _SlideTransform()

        child_offset = getattr(xfrm, "chOff", None)
        child_extent = getattr(xfrm, "chExt", None)
        if child_offset is None or child_extent is None:
            return _SlideTransform()

        try:
            offset_x = float(xfrm.x)
            offset_y = float(xfrm.y)
            extent_x = float(xfrm.cx)
            extent_y = float(xfrm.cy)
            child_offset_x = float(child_offset.x)
            child_offset_y = float(child_offset.y)
            child_extent_x = float(child_extent.cx)
            child_extent_y = float(child_extent.cy)
        except Exception:
            return _SlideTransform()

        if (
            extent_x <= 0
            or extent_y <= 0
            or child_extent_x <= 0
            or child_extent_y <= 0
        ):
            return _SlideTransform()

        scale_x = extent_x / child_extent_x
        scale_y = extent_y / child_extent_y
        return _SlideTransform(
            scale_x=scale_x,
            scale_y=scale_y,
            translate_x=offset_x - child_offset_x * scale_x,
            translate_y=offset_y - child_offset_y * scale_y,
        )