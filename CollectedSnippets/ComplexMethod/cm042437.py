def _configure_shader_color(state: ShaderState, color: Optional[rl.Color],
                            gradient: Gradient | None, origin_rect: rl.Rectangle):
  assert (color is not None) != (gradient is not None), "Either color or gradient must be provided"

  use_gradient = 1 if (gradient is not None and len(gradient.colors) >= 1) else 0
  state.use_gradient_ptr[0] = use_gradient
  rl.set_shader_value(state.shader, state.locations['useGradient'], state.use_gradient_ptr, UNIFORM_INT)

  if use_gradient:
    gradient = cast(Gradient, gradient)
    state.color_count_ptr[0] = len(gradient.colors)
    for i in range(len(gradient.colors)):
      c = gradient.colors[i]
      base = i * 4
      state.gradient_colors_ptr[base:base + 4] = [c.r / 255.0, c.g / 255.0, c.b / 255.0, c.a / 255.0]
    rl.set_shader_value_v(state.shader, state.locations['gradientColors'], state.gradient_colors_ptr, UNIFORM_VEC4, len(gradient.colors))

    for i in range(len(gradient.stops)):
      s = float(gradient.stops[i])
      state.gradient_stops_ptr[i] = 0.0 if s < 0.0 else 1.0 if s > 1.0 else s
    rl.set_shader_value_v(state.shader, state.locations['gradientStops'], state.gradient_stops_ptr, UNIFORM_FLOAT, len(gradient.stops))
    rl.set_shader_value(state.shader, state.locations['gradientColorCount'], state.color_count_ptr, UNIFORM_INT)

    # Map normalized start/end to screen pixels
    start_vec = rl.Vector2(origin_rect.x + gradient.start[0] * origin_rect.width, origin_rect.y + gradient.start[1] * origin_rect.height)
    end_vec = rl.Vector2(origin_rect.x + gradient.end[0] * origin_rect.width, origin_rect.y + gradient.end[1] * origin_rect.height)
    rl.set_shader_value(state.shader, state.locations['gradientStart'], start_vec, UNIFORM_VEC2)
    rl.set_shader_value(state.shader, state.locations['gradientEnd'], end_vec, UNIFORM_VEC2)
  else:
    color = color or rl.WHITE
    state.fill_color_ptr[0:4] = [color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0]
    rl.set_shader_value(state.shader, state.locations['fillColor'], state.fill_color_ptr, UNIFORM_VEC4)