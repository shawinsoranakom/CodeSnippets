def wait_for_execution(self, prompt_id: str, timeout: float = 120.0) -> dict:
        """
        Wait for execution to complete via WebSocket.

        Returns:
            dict with keys: completed, error, preview_count, execution_time
        """
        result = {
            "completed": False,
            "error": None,
            "preview_count": 0,
            "execution_time": 0.0
        }

        start_time = time.time()
        self.ws.settimeout(timeout)

        try:
            while True:
                out = self.ws.recv()
                elapsed = time.time() - start_time

                if isinstance(out, str):
                    message = json.loads(out)
                    msg_type = message.get("type")
                    data = message.get("data", {})

                    if data.get("prompt_id") != prompt_id:
                        continue

                    if msg_type == "executing":
                        if data.get("node") is None:
                            # Execution complete
                            result["completed"] = True
                            result["execution_time"] = elapsed
                            break

                    elif msg_type == "execution_error":
                        result["error"] = data
                        result["execution_time"] = elapsed
                        break

                    elif msg_type == "progress":
                        # Progress update during sampling
                        pass

                elif isinstance(out, bytes):
                    # Binary data = preview image
                    result["preview_count"] += 1

        except websocket.WebSocketTimeoutException:
            result["error"] = "Timeout waiting for execution"
            result["execution_time"] = time.time() - start_time

        return result