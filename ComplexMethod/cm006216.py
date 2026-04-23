def make_request(self, message_type="simple", tag_suffix=""):
        """Make a request with proper error handling and timing."""
        message = TEST_MESSAGES.get(message_type, TEST_MESSAGES["simple"])

        # Langflow API payload structure
        payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": {},
        }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.request_count += 1
        endpoint = f"/api/v1/run/{self.flow_id}?stream=false"
        name = f"{endpoint} [{message_type}{tag_suffix}]"

        try:
            with self.client.post(
                endpoint,
                json=payload,
                headers=headers,
                name=name,
                timeout=self.REQUEST_TIMEOUT,
                catch_response=True,
            ) as response:
                # Get response text for error logging
                try:
                    response_text = response.text
                except Exception:
                    response_text = "Could not read response text"

                # Handle successful responses
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Langflow API success check - look for outputs
                        if data.get("outputs"):
                            return response.success()
                        # Check for error messages in the response
                        error_msg = data.get("detail", "Unknown error")

                        # Log detailed error for successful HTTP but failed flow execution
                        log_detailed_error(
                            user_class=self.__class__.__name__,
                            method="POST",
                            url=f"{self.host}{endpoint}",
                            status_code=response.status_code,
                            response_text=response_text,
                            request_data=payload,
                            exception=None,
                        )

                        return response.failure(f"Flow execution failed: {error_msg}")
                    except json.JSONDecodeError as e:
                        log_detailed_error(
                            user_class=self.__class__.__name__,
                            method="POST",
                            url=f"{self.host}{endpoint}",
                            status_code=response.status_code,
                            response_text=response_text,
                            request_data=payload,
                            exception=e,
                        )
                        return response.failure("Invalid JSON response")

                # Log all error responses with detailed information
                log_detailed_error(
                    user_class=self.__class__.__name__,
                    method="POST",
                    url=f"{self.host}{endpoint}",
                    status_code=response.status_code,
                    response_text=response_text,
                    request_data=payload,
                    exception=None,
                )

                # Handle specific error cases
                if response.status_code in (429, 503):
                    return response.failure(f"Backpressure/capacity: {response.status_code}")
                if response.status_code == 401:
                    return response.failure("Unauthorized - API key issue")
                if response.status_code == 404:
                    return response.failure("Flow not found - check FLOW_ID")
                if response.status_code >= 500:
                    return response.failure(f"Server error {response.status_code}")

                return response.failure(f"HTTP {response.status_code}")

        except Exception as e:
            # Get more detailed error information
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "is_timeout": "timeout" in str(e).lower(),
                "is_connection_error": "connection" in str(e).lower(),
                "is_dns_error": "name resolution" in str(e).lower() or "dns" in str(e).lower(),
            }

            # Log any exceptions that occur during the request
            log_detailed_error(
                user_class=self.__class__.__name__,
                method="POST",
                url=f"{self.host}{endpoint}",
                status_code=0,  # Connection error
                response_text=f"Connection Error: {error_details}",
                request_data=payload,
                exception=str(e),
                traceback=traceback.format_exc(),
            )
            # Re-raise the exception so Locust can handle it properly
            raise