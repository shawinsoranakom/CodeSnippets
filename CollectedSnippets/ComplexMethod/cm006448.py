async def get_client(cls, user_id=None, session=None):
        """Get or create an ElevenLabs client with the API key."""
        if cls._instance is None:
            if cls._api_key is None and user_id and session:
                variable_service = get_variable_service()
                try:
                    cls._api_key = await variable_service.get_variable(
                        user_id=user_id,
                        name="ELEVENLABS_API_KEY",
                        field="elevenlabs_api_key",
                        session=session,
                    )
                except (InvalidToken, ValueError) as e:
                    await logger.aerror(f"Error with ElevenLabs API key: {e}")
                    cls._api_key = os.getenv("ELEVENLABS_API_KEY", "")
                    if not cls._api_key:
                        await logger.aerror("ElevenLabs API key not found")
                        return None
                except (KeyError, AttributeError, sqlalchemy.exc.SQLAlchemyError) as e:
                    await logger.aerror(f"Exception getting ElevenLabs API key: {e}")
                    return None

            if cls._api_key:
                cls._instance = ElevenLabs(api_key=cls._api_key)

        return cls._instance