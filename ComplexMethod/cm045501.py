async def _handle_elicitation_response(self, message: Dict[str, Any]) -> None:
        """Handle user response to elicitation request"""
        request_id = message.get("request_id")

        if not request_id:
            await self.send_message(
                {
                    "type": "error",
                    "error": "Missing request_id in elicitation response",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            return

        if request_id in self.pending_elicitations:
            try:
                action = message.get("action", "cancel")
                data = message.get("data", {})

                if action == "accept":
                    result = ElicitResult(action="accept", content=data)
                elif action == "decline":
                    result = ElicitResult(action="decline")
                else:
                    result = ElicitResult(action="cancel")

                future = self.pending_elicitations[request_id]
                if not future.done():
                    future.set_result(result)
                else:
                    logger.warning(f"Future for elicitation request {request_id} was already done")

            except Exception as e:
                error_msg = extract_real_error(e)
                logger.error(f"Error processing elicitation response: {error_msg}")

                future = self.pending_elicitations.get(request_id)
                if future and not future.done():
                    future.set_result(
                        ErrorData(code=-32603, message=f"Error processing elicitation response: {error_msg}")
                    )
        else:
            logger.warning(f"Unknown elicitation request_id: {request_id}")
            await self.send_message(
                {
                    "type": "operation_error",
                    "error": f"Unknown elicitation request_id: {request_id}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )