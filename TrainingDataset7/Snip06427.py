def get_content_type(self, obj=None, id=None, using=None, model=None):
        if obj is not None:
            return ContentType.objects.db_manager(obj._state.db).get_for_model(
                obj, for_concrete_model=self.for_concrete_model
            )
        elif id is not None:
            return ContentType.objects.db_manager(using).get_for_id(id)
        elif model is not None:
            return ContentType.objects.db_manager(using).get_for_model(
                model, for_concrete_model=self.for_concrete_model
            )
        else:
            # This should never happen. I love comments like this, don't you?
            raise Exception("Impossible arguments to GFK.get_content_type!")