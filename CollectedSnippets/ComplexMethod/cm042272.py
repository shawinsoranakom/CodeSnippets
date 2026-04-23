def _calculate_arc_data(
    self, delta: float, size: float, x: float, y: float, sin_val: float, diff_val: float, is_horizontal: bool
  ):
    """Calculate arc data and pre-compute arc points."""
    if size <= 0:
      return None

    thickness = ARC_THICKNESS_DEFAULT + ARC_THICKNESS_EXTEND * min(1.0, diff_val * 5.0)
    start_angle = (90 if sin_val > 0 else -90) if is_horizontal else (0 if sin_val > 0 else 180)
    x = min(x + delta, x) if is_horizontal else x
    y = y if is_horizontal else min(y + delta, y)

    arc_data = ArcData(
      x=x,
      y=y,
      width=size if is_horizontal else ARC_LENGTH,
      height=ARC_LENGTH if is_horizontal else size,
      thickness=thickness,
    )

    # Pre-calculate arc points
    angles = ARC_ANGLES + np.deg2rad(start_angle)

    center_x = x + arc_data.width / 2
    center_y = y + arc_data.height / 2
    radius_x = arc_data.width / 2
    radius_y = arc_data.height / 2

    x_coords = center_x + np.cos(angles) * radius_x
    y_coords = center_y - np.sin(angles) * radius_y

    arc_lines = self.h_arc_lines if is_horizontal else self.v_arc_lines
    for i, (x_coord, y_coord) in enumerate(zip(x_coords, y_coords, strict=True)):
      arc_lines[i].x = x_coord
      arc_lines[i].y = y_coord

    return arc_data