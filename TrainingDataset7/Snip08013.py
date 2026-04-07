async def aclear_expired(cls):
        await cls.get_model_class().objects.filter(
            expire_date__lt=timezone.now()
        ).adelete()