def check_mouse_position():
    global exit_flag
    corner_threshold = 10
    screen_width, screen_height = pyautogui.size()

    while not exit_flag:
        x, y = pyautogui.position()
        if (
            (x <= corner_threshold and y <= corner_threshold)
            or (x <= corner_threshold and y >= screen_height - corner_threshold)
            or (x >= screen_width - corner_threshold and y <= corner_threshold)
            or (
                x >= screen_width - corner_threshold
                and y >= screen_height - corner_threshold
            )
        ):
            exit_flag = True
            print("\nMouse moved to corner. Exiting...")
            os._exit(0)
        threading.Event().wait(0.1)