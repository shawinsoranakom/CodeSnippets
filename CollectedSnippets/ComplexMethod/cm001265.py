async def ask(request: ChatRequest, user_id: str) -> ApiResponse:
        """
        Send request to Otto API and handle the response.
        """
        # Check if Otto API URL is configured
        if not OTTO_API_URL:
            logger.error("Otto API URL is not configured")
            raise HTTPException(
                status_code=503, detail="Otto service is not configured"
            )

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }

                # If graph data is requested, fetch it
                graph_data = await OttoService._fetch_graph_data(request, user_id)

                # Prepare the payload with optional graph data
                payload = {
                    "query": request.query,
                    "conversation_history": [
                        msg.model_dump() for msg in request.conversation_history
                    ],
                    "user_id": user_id,
                    "message_id": request.message_id,
                }

                if graph_data:
                    payload["graph_data"] = graph_data.model_dump()

                logger.info(f"Sending request to Otto API for user {user_id}")
                logger.debug(f"Request payload: {payload}")

                async with session.post(
                    OTTO_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Otto API error: {error_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Otto API request failed: {error_text}",
                        )

                    data = await response.json()
                    logger.info(
                        f"Successfully received response from Otto API for user {user_id}"
                    )
                    return ApiResponse(**data)

        except aiohttp.ClientError as e:
            logger.error(f"Connection error to Otto API: {str(e)}")
            raise HTTPException(
                status_code=503, detail="Failed to connect to Otto service"
            )
        except asyncio.TimeoutError:
            logger.error("Timeout error connecting to Otto API after 60 seconds")
            raise HTTPException(
                status_code=504, detail="Request to Otto service timed out"
            )
        except Exception as e:
            logger.error(f"Unexpected error in Otto API proxy: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Internal server error in Otto proxy"
            )