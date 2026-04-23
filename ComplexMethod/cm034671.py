def run(cls, method: str, session: StreamSession, prompt: str, conversation: JsonConversation, media: list = None):
            headers = {
                "content-type": "application/json",
                "x-zerogpu-token": conversation.zerogpu_token,
                "x-zerogpu-uuid": conversation.zerogpu_uuid,
                "referer": cls.referer,
            }
            if method == "predict":
                return session.post(f"{cls.api_url}/gradio_api/run/predict", **{
                    "headers": {k: v for k, v in headers.items() if v is not None},
                    "json": {
                        "data":[
                            [],
                            {
                                "text": prompt,
                                "files": media,
                            },
                            None
                        ],
                        "event_data": None,
                        "fn_index": 10,
                        "trigger_id": 8,
                        "session_hash": conversation.session_hash
                    },
                })
            if method == "post":
                return session.post(f"{cls.api_url}/gradio_api/queue/join?__theme=light", **{
                    "headers": {k: v for k, v in headers.items() if v is not None},
                    "json": {
                        "data": [[
                                {
                                "role": "user",
                                "content": prompt,
                                }
                            ]] + [[
                                {
                                    "role": "user",
                                    "content": {"file": image}
                                } for image in media
                            ]],
                        "event_data": None,
                        "fn_index": 11,
                        "trigger_id": 8,
                        "session_hash": conversation.session_hash
                    },
                })
            return session.get(f"{cls.api_url}/gradio_api/queue/data?session_hash={conversation.session_hash}", **{
                "headers": {
                    "accept": "text/event-stream",
                    "content-type": "application/json",
                    "referer": cls.referer,
                }
            })