async def _ask(self, agent: Agent, prompt: str) -> str:
        """Run an ADK agent with a prompt, return text response."""
        self._call_id += 1
        uid = f"u{self._call_id}"
        runner = Runner(
            agent=agent, app_name="skill_opt", session_service=self._session_service
        )
        session = await self._session_service.create_session(
            app_name="skill_opt", user_id=uid
        )
        text = ""
        async for event in runner.run_async(
            user_id=uid,
            session_id=session.id,
            new_message=types.Content(parts=[types.Part(text=prompt)]),
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts or []:
                    if hasattr(part, "text") and part.text:
                        text += part.text
        return text