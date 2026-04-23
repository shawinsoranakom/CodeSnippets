def get_forward_related_filter(self, obj):
        """See corresponding method on RelatedField"""
        return {
            self.fk_field: obj.pk,
            self.ct_field: ContentType.objects.get_for_model(obj).pk,
        }