async def _async_get_models(
        self, self_only: bool, language: str | None, title: str | None, sort_by: str
    ) -> list[SelectOptionDict]:
        """Get the available models."""
        try:
            voices_response = await self.client.voices.list(
                self_only=self_only,
                language=language
                if language and language.strip() and language != "Any"
                else None,
                title=title if title and title.strip() else None,
                sort_by=sort_by,
            )
        except Exception as exc:
            raise CannotGetModelsError(exc) from exc

        voices = voices_response.items

        return [
            SelectOptionDict(
                value=voice.id,
                label=f"{voice.title} - {voice.task_count} uses",
            )
            for voice in voices
        ]