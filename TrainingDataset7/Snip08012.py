def clear_expired(cls):
        cls.get_model_class().objects.filter(expire_date__lt=timezone.now()).delete()