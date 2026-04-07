def log_actions(
        self, user_id, queryset, action_flag, change_message="", *, single_object=False
    ):
        if isinstance(change_message, list):
            change_message = json.dumps(change_message)

        log_entry_list = [
            self.model(
                user_id=user_id,
                content_type_id=ContentType.objects.get_for_model(
                    obj, for_concrete_model=False
                ).id,
                object_id=obj.pk,
                object_repr=str(obj)[:200],
                action_flag=action_flag,
                change_message=change_message,
            )
            for obj in queryset
        ]

        if len(log_entry_list) == 1:
            instance = log_entry_list[0]
            instance.save()
            if single_object:
                return instance
            return [instance]

        return self.model.objects.bulk_create(log_entry_list)