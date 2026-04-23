def make_request(self, message_type="simple", tag_suffix=""):
        message = TEST_MESSAGES.get(message_type, TEST_MESSAGES["simple"])
        payload = {"input_value": message, "session_id": f"{self.session_id}_{self.request_count}"}
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        self.request_count += 1
        name = f"{API_ENDPOINT} [{message_type}{tag_suffix}]"

        with self.client.post(
            API_ENDPOINT,
            json=payload,
            headers=headers,
            name=name,
            timeout=self.REQUEST_TIMEOUT,
            catch_response=True,
        ) as response:
            # Handle successful responses
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    return response.failure("Invalid JSON response")

                # Strictly check for success=True in the response payload
                success = data.get("success")
                if success is True:
                    return response.success()

                # Application-level failure - success is False, None, or missing
                msg = str(data.get("result", "Unknown error"))[:200]
                success_status = f"success={success}" if success is not None else "success=missing"
                return response.failure(f"Flow failed ({success_status}): {msg}")

            if response.status_code in (429, 503):
                return response.failure(f"Backpressure: {response.status_code}")
            if response.status_code == 401:
                return response.failure("Unauthorized")
            if response.status_code == 404:
                return response.failure("Not Found - possible bad FLOW_ID or misconfiguration")
            if response.status_code >= 500:
                return response.failure(f"Server error {response.status_code}")
            return response.failure(f"HTTP {response.status_code}")