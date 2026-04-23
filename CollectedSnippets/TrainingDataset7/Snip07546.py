def verify_fk(self, feat, rel_model, rel_mapping):
        """
        Given an OGR Feature, the related model and its dictionary mapping,
        retrieve the related model for the ForeignKey mapping.
        """
        # TODO: It is expensive to retrieve a model for every record --
        #  explore if an efficient mechanism exists for caching related
        #  ForeignKey models.

        # Constructing and verifying the related model keyword arguments.
        fk_kwargs = {}
        for field_name, ogr_name in rel_mapping.items():
            fk_kwargs[field_name] = self.verify_ogr_field(
                feat[ogr_name], rel_model._meta.get_field(field_name)
            )

        # Attempting to retrieve and return the related model.
        try:
            return rel_model.objects.using(self.using).get(**fk_kwargs)
        except ObjectDoesNotExist:
            raise MissingForeignKey(
                "No ForeignKey %s model found with keyword arguments: %s"
                % (rel_model.__name__, fk_kwargs)
            )