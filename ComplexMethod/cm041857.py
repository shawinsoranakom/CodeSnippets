def _capture_output(self, message_queue):
        while True:
            time.sleep(0.1)

            # For async usage
            if (
                hasattr(self.computer.interpreter, "stop_event")
                and self.computer.interpreter.stop_event.is_set()
            ):
                self.finish_flag = True
                break

            if self.listener_thread:
                try:
                    output = message_queue.get(timeout=0.1)
                    if DEBUG_MODE:
                        print(output)
                    yield output

                except queue.Empty:
                    if self.finish_flag:
                        time.sleep(0.1)

                        try:
                            output = message_queue.get(timeout=0.1)
                            if DEBUG_MODE:
                                print(output)
                            yield output
                        except queue.Empty:
                            if DEBUG_MODE:
                                print("we're done")
                            break