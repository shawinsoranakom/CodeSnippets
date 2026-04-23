def iopub_message_listener():
            max_retries = 100
            while True:
                # If self.finish_flag = True, and we didn't set it (we do below), we need to stop. That's our "stop"
                if self.finish_flag == True:
                    if DEBUG_MODE:
                        print("interrupting kernel!!!!!")
                    self.km.interrupt_kernel()
                    return
                # For async usage
                if (
                    hasattr(self.computer.interpreter, "stop_event")
                    and self.computer.interpreter.stop_event.is_set()
                ):
                    self.km.interrupt_kernel()
                    self.finish_flag = True
                    return
                try:
                    input_patience = int(
                        os.environ.get("INTERPRETER_TERMINAL_INPUT_PATIENCE", 15)
                    )
                    if (
                        time.time() - self.last_output_time > input_patience
                        and time.time() - self.last_output_message_time > input_patience
                    ):
                        self.last_output_message_time = time.time()

                        text = f"{self.computer.interpreter.messages}\n\nThe program above has been running for over 15 seconds. It might require user input. Are there keystrokes that the user should type in, to proceed after the last command?"
                        if time.time() - self.last_output_time > 500:
                            text += f" If you think the process is frozen, or that the user wasn't expect it to run for this long (it has been {time.time() - self.last_output_time} seconds since last output) then say <input>CTRL-C</input>."

                        messages = [
                            {
                                "role": "system",
                                "type": "message",
                                "content": "You are an expert programming assistant. You will help the user determine if they should enter input into the terminal, per the user's requests. If you think the user would want you to type something into stdin, enclose it in <input></input> XML tags, like <input>y</input> to type 'y'.",
                            },
                            {"role": "user", "type": "message", "content": text},
                        ]
                        params = {
                            "messages": messages,
                            "model": self.computer.interpreter.llm.model,
                            "stream": True,
                            "temperature": 0,
                        }
                        if self.computer.interpreter.llm.api_key:
                            params["api_key"] = self.computer.interpreter.llm.api_key

                        response = ""
                        for chunk in litellm.completion(**params):
                            content = chunk.choices[0].delta.content
                            if type(content) == str:
                                response += content

                        # Parse the response for input tags
                        input_match = re.search(r"<input>(.*?)</input>", response)
                        if input_match:
                            user_input = input_match.group(1)
                            # Check if the user input is CTRL-C
                            self.finish_flag = True
                            if user_input.upper() == "CTRL-C":
                                self.finish_flag = True
                            else:
                                self.kc.input(user_input)

                    msg = self.kc.iopub_channel.get_msg(timeout=0.05)
                    self.last_output_time = time.time()
                except queue.Empty:
                    continue
                except Exception as e:
                    max_retries -= 1
                    if max_retries < 0:
                        raise
                    print("Jupyter error, retrying:", str(e))
                    continue

                if DEBUG_MODE:
                    print("-----------" * 10)
                    print("Message received:", msg["content"])
                    print("-----------" * 10)

                if (
                    msg["header"]["msg_type"] == "status"
                    and msg["content"]["execution_state"] == "idle"
                ):
                    # Set finish_flag and return when the kernel becomes idle
                    if DEBUG_MODE:
                        print("from thread: kernel is idle")
                    self.finish_flag = True
                    return

                content = msg["content"]

                if msg["msg_type"] == "stream":
                    line, active_line = self.detect_active_line(content["text"])
                    if active_line:
                        message_queue.put(
                            {
                                "type": "console",
                                "format": "active_line",
                                "content": active_line,
                            }
                        )
                    message_queue.put(
                        {"type": "console", "format": "output", "content": line}
                    )
                elif msg["msg_type"] == "error":
                    content = "\n".join(content["traceback"])
                    # Remove color codes
                    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
                    content = ansi_escape.sub("", content)
                    message_queue.put(
                        {
                            "type": "console",
                            "format": "output",
                            "content": content,
                        }
                    )
                elif msg["msg_type"] in ["display_data", "execute_result"]:
                    data = content["data"]
                    if "image/png" in data:
                        message_queue.put(
                            {
                                "type": "image",
                                "format": "base64.png",
                                "content": data["image/png"],
                            }
                        )
                    elif "image/jpeg" in data:
                        message_queue.put(
                            {
                                "type": "image",
                                "format": "base64.jpeg",
                                "content": data["image/jpeg"],
                            }
                        )
                    elif "text/html" in data:
                        message_queue.put(
                            {
                                "type": "code",
                                "format": "html",
                                "content": data["text/html"],
                            }
                        )
                    elif "text/plain" in data:
                        message_queue.put(
                            {
                                "type": "console",
                                "format": "output",
                                "content": data["text/plain"],
                            }
                        )
                    elif "application/javascript" in data:
                        message_queue.put(
                            {
                                "type": "code",
                                "format": "javascript",
                                "content": data["application/javascript"],
                            }
                        )