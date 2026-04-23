async def join_meeting(
        self,
        bot_name: str,
        meeting_url: str,
        reserved: bool = False,
        bot_image: Optional[str] = None,
        entry_message: Optional[str] = None,
        start_time: Optional[int] = None,
        speech_to_text: Optional[Dict[str, Any]] = None,
        webhook_url: Optional[str] = None,
        automatic_leave: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
        recording_mode: str = "speaker_view",
        streaming: Optional[Dict[str, Any]] = None,
        deduplication_key: Optional[str] = None,
        zoom_sdk_id: Optional[str] = None,
        zoom_sdk_pwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deploy a bot to join and record a meeting.

        POST /bots
        """
        body = {
            "bot_name": bot_name,
            "meeting_url": meeting_url,
            "reserved": reserved,
            "recording_mode": recording_mode,
        }

        # Add optional fields if provided
        if bot_image is not None:
            body["bot_image"] = bot_image
        if entry_message is not None:
            body["entry_message"] = entry_message
        if start_time is not None:
            body["start_time"] = start_time
        if speech_to_text is not None:
            body["speech_to_text"] = speech_to_text
        if webhook_url is not None:
            body["webhook_url"] = webhook_url
        if automatic_leave is not None:
            body["automatic_leave"] = automatic_leave
        if extra is not None:
            body["extra"] = extra
        if streaming is not None:
            body["streaming"] = streaming
        if deduplication_key is not None:
            body["deduplication_key"] = deduplication_key
        if zoom_sdk_id is not None:
            body["zoom_sdk_id"] = zoom_sdk_id
        if zoom_sdk_pwd is not None:
            body["zoom_sdk_pwd"] = zoom_sdk_pwd

        response = await self.requests.post(
            f"{self.BASE_URL}/bots",
            headers=self.headers,
            json=body,
        )
        return response.json()