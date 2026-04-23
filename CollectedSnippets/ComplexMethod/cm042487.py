def wheel_poll_thread(q: 'Queue[str]') -> NoReturn:
  # Open the joystick device.
  fn = '/dev/input/js0'
  print(f'Opening {fn}...')
  jsdev = open(fn, 'rb')

  # Get the device name.
  #buf = bytearray(63)
  buf = array.array('B', [0] * 64)
  ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf)  # JSIOCGNAME(len)
  js_name = buf.tobytes().rstrip(b'\x00').decode('utf-8')
  print(f'Device name: {js_name}')

  # Get number of axes and buttons.
  buf = array.array('B', [0])
  ioctl(jsdev, 0x80016a11, buf)  # JSIOCGAXES
  num_axes = buf[0]

  buf = array.array('B', [0])
  ioctl(jsdev, 0x80016a12, buf)  # JSIOCGBUTTONS
  num_buttons = buf[0]

  # Get the axis map.
  buf = array.array('B', [0] * 0x40)
  ioctl(jsdev, 0x80406a32, buf)  # JSIOCGAXMAP

  for _axis in buf[:num_axes]:
    axis_name = axis_names.get(_axis, f'unknown(0x{_axis:02x})')
    axis_name_list.append(axis_name)
    axis_states[axis_name] = 0.0

  # Get the button map.
  buf = array.array('H', [0] * 200)
  ioctl(jsdev, 0x80406a34, buf)  # JSIOCGBTNMAP

  for btn in buf[:num_buttons]:
    btn_name = button_names.get(btn, f'unknown(0x{btn:03x})')
    button_name_list.append(btn_name)
    button_states[btn_name] = 0

  print(f'{num_axes} axes found: {", ".join(axis_name_list)}')
  print(f'{num_buttons} buttons found: {", ".join(button_name_list)}')

  # Enable FF
  import evdev
  from evdev import ecodes, InputDevice
  device = evdev.list_devices()[0]
  evtdev = InputDevice(device)
  val = 24000
  evtdev.write(ecodes.EV_FF, ecodes.FF_AUTOCENTER, val)

  while True:
    evbuf = jsdev.read(8)
    value, mtype, number = struct.unpack('4xhBB', evbuf)
    # print(mtype, number, value)
    if mtype & 0x02:  # wheel & paddles
      axis = axis_name_list[number]

      if axis == "z":  # gas
        fvalue = value / 32767.0
        axis_states[axis] = fvalue
        normalized = (1 - fvalue) * 50
        q.put(control_cmd_gen(f"throttle_{normalized:f}"))

      elif axis == "rz":  # brake
        fvalue = value / 32767.0
        axis_states[axis] = fvalue
        normalized = (1 - fvalue) * 50
        q.put(control_cmd_gen(f"brake_{normalized:f}"))

      elif axis == "x":  # steer angle
        fvalue = value / 32767.0
        axis_states[axis] = fvalue
        normalized = fvalue
        q.put(control_cmd_gen(f"steer_{normalized:f}"))

    elif mtype & 0x01:  # buttons
      if value == 1: # press down
        if number in [0, 19]:  # X
          q.put(control_cmd_gen("cruise_down"))

        elif number in [3, 18]:  # triangle
          q.put(control_cmd_gen("cruise_up"))

        elif number in [1, 6]:  # square
          q.put(control_cmd_gen("cruise_cancel"))

        elif number in [10, 21]:  # R3
          q.put(control_cmd_gen("reverse_switch"))