async def _aget_session_from_db(self):
        try:
            return await self.model.objects.aget(
                session_key=self.session_key, expire_date__gt=timezone.now()
            )
        except (self.model.DoesNotExist, SuspiciousOperation) as e:
            if isinstance(e, SuspiciousOperation):
                logger = logging.getLogger("django.security.%s" % e.__class__.__name__)
                logger.warning(str(e))
            self._session_key = None