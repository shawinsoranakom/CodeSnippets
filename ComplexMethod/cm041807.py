def main():
    ### GET OPTIONAL CUSTOM MESSAGE

    custom_message = None
    if len(sys.argv) > 1:
        custom_message = "wtf " + " ".join(sys.argv[1:])

    ### GET TERMINAL HISTORY

    keyboard = Controller()
    history = None

    ## SELECT ALL AND COPY METHOD

    if True:
        # Save clipboard
        clipboard = pyperclip.paste()

        # Select all text
        shortcut_key = Key.cmd if platform.system() == "Darwin" else Key.ctrl
        with keyboard.pressed(shortcut_key):
            keyboard.press("a")
            keyboard.release("a")

        # Copy selected text
        with keyboard.pressed(shortcut_key):
            keyboard.press("c")
            keyboard.release("c")

        # Deselect
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)

        # Wait for the clipboard to update
        time.sleep(0.1)

        # Get terminal history from clipboard
        history = pyperclip.paste()

        # Reset clipboard to stored one
        pyperclip.copy(clipboard)

    ## OCR SCREENSHOT METHOD

    if not history:
        try:
            import pytesseract
            from PIL import ImageGrab

            # Get active window coordinates using platform-specific methods
            platform_name = platform.system()
            if platform_name == "Windows":
                import win32gui

                window = win32gui.GetForegroundWindow()
                left, top, right, bottom = win32gui.GetWindowRect(window)
            elif platform_name == "Darwin":
                from Quartz import (
                    CGWindowListCopyWindowInfo,
                    kCGNullWindowID,
                    kCGWindowListOptionOnScreenOnly,
                )

                window_info = CGWindowListCopyWindowInfo(
                    kCGWindowListOptionOnScreenOnly, kCGNullWindowID
                )
                for window in window_info:
                    if window["kCGWindowLayer"] == 0:
                        window_geometry = window["kCGWindowBounds"]
                        left = window_geometry["X"]
                        top = window_geometry["Y"]
                        right = int(left + window_geometry["Width"])
                        bottom = int(top + window_geometry["Height"])
                        break
            else:  # Assume it's a Linux-based system
                root = subprocess.Popen(
                    ["xprop", "-root", "_NET_ACTIVE_WINDOW"], stdout=subprocess.PIPE
                )
                stdout, stderr = root.communicate()
                m = re.search(b"^_NET_ACTIVE_WINDOW.* ([\\w]+)$", stdout)
                if m is not None:
                    window_id = m.group(1)
                    window = subprocess.Popen(
                        ["xwininfo", "-id", window_id], stdout=subprocess.PIPE
                    )
                    stdout, stderr = window.communicate()
                    match = re.search(
                        rb"Absolute upper-left X:\s*(\d+).*Absolute upper-left Y:\s*(\d+).*Width:\s*(\d+).*Height:\s*(\d+)",
                        stdout,
                        re.DOTALL,
                    )
                    if match is not None:
                        left, top, width, height = map(int, match.groups())
                        right = left + width
                        bottom = top + height

            # spinner.stop()
            # print("\nPermission to capture terminal commands via screenshot -> OCR?")
            # permission = input("(y/n) > ")
            # print("")
            # if permission.lower() != 'y':
            #     print("Exiting...")
            #     exit()
            # spinner.start()

            # Take screenshot of the active window
            screenshot = ImageGrab.grab(
                bbox=(int(left), int(top), int(right), int(bottom))
            )

            # OCR the screenshot to get the text
            text = pytesseract.image_to_string(screenshot)

            history = text

            if "wtf" in history:
                last_wtf_index = history.rindex("wtf")
                history = history[:last_wtf_index]
        except ImportError:
            spinner.stop()
            print(
                "To use OCR to capture terminal output (recommended) run `pip install pytesseract` or `pip3 install pytesseract`."
            )
            spinner.start()

    ## TERMINAL HISTORY METHOD

    if not history:
        try:
            shell = os.environ.get("SHELL", "/bin/bash")
            command = [shell, "-ic", "fc -ln -10"]  # Get just the last command

            output = subprocess.check_output(command, stderr=subprocess.STDOUT).decode(
                "utf-8"
            )

            # Split the output into lines
            lines = output.strip().split("\n")

            # Filter out lines that look like the "saving session" message
            history = [
                line
                for line in lines
                if not line.startswith("...")
                and "saving" not in line
                and "Saving session..." not in line
            ]
            history = [l.strip() for l in history if l.strip()][-10:]

            # Split the history into individual commands

            # Get the last command
            last_command = history[-1]
            spinner.start()
            print(
                f"\nRunning the last command again to collect its output: {last_command}\n"
            )
            spinner.stop()
            # Run the last command and collect its output
            try:
                last_command_output = subprocess.check_output(
                    last_command, shell=True, stderr=subprocess.STDOUT
                ).decode("utf-8")
            except subprocess.CalledProcessError as e:
                last_command_output = e.output.decode("utf-8")
            except Exception as e:
                last_command_output = str(e)

            # Format the history
            history = "The user tried to run the following commands:\n" + "\n".join(
                history
            )
            history += f"\nThe last command, {last_command}, resulted in this output:\n{last_command_output}"

        except Exception as e:
            raise
            print(
                "Failed to retrieve and run the last command from terminal history. Exiting."
            )
            return

    # Trim history
    history = history[-9000:].strip()

    # Remove any trailing spinner commands
    spinner_commands = [
        "⠴",
        "⠦",
        "⠇",
        "⠉",
        "⠙",
        "⠸",
        "⠼",
        "⠤",
        "⠴",
        "⠂",
        "⠄",
        "⠈",
        "⠐",
        "⠠",
    ]
    for command in spinner_commands:
        if history.endswith(command):
            history = history[: -len(command)].strip()
            break

    if "wtf" in history:
        last_wtf_index = history.rindex("wtf")
        history = history[:last_wtf_index]

    ### GET ERROR CONTEXT

    # Regex pattern to extract filename and line number
    pattern = r'File "([^"]+)", line (\d+)'
    matches = re.findall(pattern, history)

    # Only keep the last X matches
    matches = matches[-1:]  # Just the last match, change -1 to get more

    # Function to get specified lines from a file
    def get_lines_from_file(filename, line_number):
        lines = []
        try:
            with open(filename, "r") as file:
                all_lines = file.readlines()
                start_line = max(0, line_number - 3)  # Preceding lines
                end_line = min(len(all_lines), line_number + 2)  # Following lines
                for i in range(start_line, end_line + 1):
                    lines.append(f"Line {i+1}: " + all_lines[i].rstrip())
        except Exception as e:
            lines.append(f"Error reading file: {e}")
        return lines

    # Create the dictionary with filename, line number, and text
    result = []
    for match in matches:
        filename, line_number = match
        line_number = int(line_number)
        lines = get_lines_from_file(filename, line_number)
        result.append({"filename": filename, "text": "\n".join(lines)})

    if result != []:
        history = "Terminal: " + history

    # Add context
    for entry in result:
        history = f"""File: {entry["filename"]}\n{entry["text"]}\n\n""" + history

    ### PREPARE FOR LLM

    # Get LLM model from profile
    default_profile_path = os.path.join(
        platformdirs.user_config_dir("open-interpreter"), "profiles", "default.yaml"
    )

    try:
        with open(default_profile_path, "r") as file:
            profile = yaml.safe_load(file)
            wtf_model = profile.get("wtf", {}).get("model")
            if wtf_model:
                model = wtf_model
            else:
                model = profile.get("llm", {}).get("model", "gpt-4o-mini")
    except:
        model = "gpt-4o-mini"

    # If they're using a local model (improve this heuristic) use the LOCAL_SYSTEM_MESSAGE
    if "ollama" in model or "llama" in model:
        system_message = LOCAL_SYSTEM_MESSAGE
    else:
        system_message = SYSTEM_MESSAGE

    # If they passed in a custom message, use the CUSTOM_MESSAGE_SYSTEM_MESSAGE
    if custom_message:
        system_message = CUSTOM_MESSAGE_SYSTEM_MESSAGE
        user_message = (
            "Answer THIS question by telling me what code to run:"
            + custom_message
            + "\nMy terminal history, which may or may not be relevant, is this:\n---\n"
            + history
            + "\n---\nPlease now answer THIS question by telling me what code to run: "
            + custom_message
        )
    else:
        user_message = (
            history.strip()
            + "\n\nPlease help me resolve the final error above by telling me what code to run in a markdown code block."
        )

    # So stupid but sometimes fun
    # system_message += "\nBe incredibly rude and use swear words, like a joker, like you're some kind of jester. You can say 'Fuck' and 'Fucking'. This is for adults. Be funny. USE ALL LOWER CASE. Act like you're an aggreived pair programmer to the idiot that got themselves in this situation."

    messages = [
        {"role": "system", "content": system_message.strip()},
        {"role": "user", "content": user_message.strip()},
    ]

    # DEBUGGING: PRINT MESSAGES

    # print("---")
    # import pprint
    # pprint.pprint(messages)
    # print("---")
    # time.sleep(100)

    ### PARSE LLM RESPONSE

    in_code = False
    backtick_count = 0
    language_buffer = ""
    started = False

    for chunk in litellm.completion(
        model=model, messages=messages, temperature=0, stream=True
    ):
        if not started:
            started = True
            spinner.stop()
            print("")

        content = chunk.choices[0].delta.content
        if content:
            for char in content:
                if char == "`":
                    backtick_count += 1
                    if backtick_count == 3:
                        in_code = not in_code
                        backtick_count = 0
                        language_buffer = ""
                        if not in_code:  # We've just exited a code block
                            time.sleep(0.1)
                            print("\n")
                            return  # Exit after typing the command
                        else:  # Entered code block
                            print("Press `enter` to run: ", end="", flush=True)
                elif in_code:
                    if language_buffer is not None:
                        if char.isalnum():
                            language_buffer += char
                        elif char.isspace():
                            language_buffer = None
                    elif char not in ["\n", "\\"]:
                        keyboard.type(char)
                else:
                    if backtick_count:
                        print("`" * backtick_count, end="", flush=True)
                        backtick_count = 0

                    # if "\n" in char:
                    #     char.replace("\n", "\n    ")

                    print(char, end="", flush=True)

                    backtick_count = 0