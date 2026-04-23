async def run(self, input_data: Input, **kwargs) -> BlockOutput:
        payload = input_data.payload
        is_edited = "edited_message" in payload
        message = payload.get("message") or payload.get("edited_message", {})

        # Extract common fields
        chat = message.get("chat", {})
        sender = message.get("from", {})

        yield "payload", payload
        yield "chat_id", chat.get("id", 0)
        yield "message_id", message.get("message_id", 0)
        yield "user_id", sender.get("id", 0)
        yield "username", sender.get("username", "")
        yield "first_name", sender.get("first_name", "")
        yield "is_edited", is_edited

        # For edited messages, yield event as "edited_message" and extract
        # all content fields from the edited message body
        if is_edited:
            yield "event", "edited_message"
            yield "text", message.get("text", "")
            photos = message.get("photo", [])
            yield "photo_file_id", photos[-1].get("file_id", "") if photos else ""
            voice = message.get("voice", {})
            yield "voice_file_id", voice.get("file_id", "")
            audio = message.get("audio", {})
            yield "audio_file_id", audio.get("file_id", "")
            document = message.get("document", {})
            video = message.get("video", {})
            yield "file_id", (document.get("file_id", "") or video.get("file_id", ""))
            yield "file_name", (
                document.get("file_name", "") or audio.get("file_name", "")
            )
            yield "caption", message.get("caption", "")
        # Determine message type and extract content
        elif "text" in message:
            yield "event", "text"
            yield "text", message.get("text", "")
            yield "photo_file_id", ""
            yield "voice_file_id", ""
            yield "audio_file_id", ""
            yield "file_id", ""
            yield "file_name", ""
            yield "caption", ""
        elif "photo" in message:
            # Get the largest photo (last in array)
            photos = message.get("photo", [])
            photo_fid = photos[-1].get("file_id", "") if photos else ""
            yield "event", "photo"
            yield "text", ""
            yield "photo_file_id", photo_fid
            yield "voice_file_id", ""
            yield "audio_file_id", ""
            yield "file_id", ""
            yield "file_name", ""
            yield "caption", message.get("caption", "")
        elif "voice" in message:
            voice = message.get("voice", {})
            yield "event", "voice"
            yield "text", ""
            yield "photo_file_id", ""
            yield "voice_file_id", voice.get("file_id", "")
            yield "audio_file_id", ""
            yield "file_id", ""
            yield "file_name", ""
            yield "caption", message.get("caption", "")
        elif "audio" in message:
            audio = message.get("audio", {})
            yield "event", "audio"
            yield "text", ""
            yield "photo_file_id", ""
            yield "voice_file_id", ""
            yield "audio_file_id", audio.get("file_id", "")
            yield "file_id", ""
            yield "file_name", audio.get("file_name", "")
            yield "caption", message.get("caption", "")
        elif "document" in message:
            document = message.get("document", {})
            yield "event", "document"
            yield "text", ""
            yield "photo_file_id", ""
            yield "voice_file_id", ""
            yield "audio_file_id", ""
            yield "file_id", document.get("file_id", "")
            yield "file_name", document.get("file_name", "")
            yield "caption", message.get("caption", "")
        elif "video" in message:
            video = message.get("video", {})
            yield "event", "video"
            yield "text", ""
            yield "photo_file_id", ""
            yield "voice_file_id", ""
            yield "audio_file_id", ""
            yield "file_id", video.get("file_id", "")
            yield "file_name", video.get("file_name", "")
            yield "caption", message.get("caption", "")
        else:
            yield "event", "other"
            yield "text", ""
            yield "photo_file_id", ""
            yield "voice_file_id", ""
            yield "audio_file_id", ""
            yield "file_id", ""
            yield "file_name", ""
            yield "caption", ""