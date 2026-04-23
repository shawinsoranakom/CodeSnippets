def respond(self, run_code=None):
        for attempt in range(5):  # 5 attempts
            try:
                if run_code == None:
                    run_code = self.auto_run

                sent_chunks = False

                for chunk_og in self._respond_and_store():
                    chunk = (
                        chunk_og.copy()
                    )  # This fixes weird double token chunks. Probably a deeper problem?

                    if chunk["type"] == "confirmation":
                        if run_code:
                            run_code = False
                            continue
                        else:
                            break

                    if self.stop_event.is_set():
                        return

                    if self.print:
                        if "start" in chunk:
                            print("\n")
                        if chunk["type"] in ["code", "console"] and "format" in chunk:
                            if "start" in chunk:
                                print(
                                    "\n------------\n\n```" + chunk["format"],
                                    flush=True,
                                )
                            if "end" in chunk:
                                print("\n```\n\n------------\n\n", flush=True)
                        if chunk.get("format") != "active_line":
                            if "format" in chunk and "base64" in chunk["format"]:
                                print("\n[An image was produced]")
                            else:
                                content = chunk.get("content", "")
                                content = (
                                    str(content)
                                    .encode("ascii", "ignore")
                                    .decode("ascii")
                                )
                                print(content, end="", flush=True)

                    if self.debug:
                        print("Interpreter produced this chunk:", chunk)

                    self.output_queue.sync_q.put(chunk)
                    sent_chunks = True

                if not sent_chunks:
                    print("ERROR. NO CHUNKS SENT. TRYING AGAIN.")
                    print("Messages:", self.messages)
                    messages = [
                        "Hello? Answer please.",
                        "Just say something, anything.",
                        "Are you there?",
                        "Can you respond?",
                        "Please reply.",
                    ]
                    self.messages.append(
                        {
                            "role": "user",
                            "type": "message",
                            "content": messages[attempt % len(messages)],
                        }
                    )
                    time.sleep(1)
                else:
                    self.output_queue.sync_q.put(complete_message)
                    if self.debug:
                        print("\nServer response complete.\n")
                    return

            except Exception as e:
                error = traceback.format_exc() + "\n" + str(e)
                error_message = {
                    "role": "server",
                    "type": "error",
                    "content": traceback.format_exc() + "\n" + str(e),
                }
                self.output_queue.sync_q.put(error_message)
                self.output_queue.sync_q.put(complete_message)
                print("\n\n--- SENT ERROR: ---\n\n")
                print(error)
                print("\n\n--- (ERROR ABOVE WAS SENT) ---\n\n")
                return

        error_message = {
            "role": "server",
            "type": "error",
            "content": "No chunks sent or unknown error.",
        }
        self.output_queue.sync_q.put(error_message)
        self.output_queue.sync_q.put(complete_message)
        raise Exception("No chunks sent or unknown error.")