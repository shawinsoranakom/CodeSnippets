async def acreate_model_instance(self, data):
        """See create_model_instance()."""
        return self.model(
            session_key=await self._aget_or_create_session_key(),
            session_data=self.encode(data),
            expire_date=await self.aget_expiry_date(),
        )