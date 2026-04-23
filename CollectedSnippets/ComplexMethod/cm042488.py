def keyboard_poll_thread(q: 'Queue[QueueMessage]'):
  print_keyboard_help()

  while True:
    c = getch()
    if c == '1':
      q.put(control_cmd_gen("cruise_up"))
    elif c == '2':
      q.put(control_cmd_gen("cruise_down"))
    elif c == '3':
      q.put(control_cmd_gen("cruise_cancel"))
    elif c == 'w':
      q.put(control_cmd_gen(f"throttle_{1.0}"))
    elif c == 'a':
      q.put(control_cmd_gen(f"steer_{-0.15}"))
    elif c == 's':
      q.put(control_cmd_gen(f"brake_{1.0}"))
    elif c == 'd':
      q.put(control_cmd_gen(f"steer_{0.15}"))
    elif c == 'z':
      q.put(control_cmd_gen("blinker_left"))
    elif c == 'x':
      q.put(control_cmd_gen("blinker_right"))
    elif c == 'i':
      q.put(control_cmd_gen("ignition"))
    elif c == 'r':
      q.put(control_cmd_gen("reset"))
    elif c == 'q':
      q.put(control_cmd_gen("quit"))
      break
    else:
      print_keyboard_help()