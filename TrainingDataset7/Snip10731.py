def can_fast_delete(self, objs, from_field=None):
        """
        Determine if the objects in the given queryset-like or single object
        can be fast-deleted. This can be done if there are no cascades, no
        parents and no signal listeners for the object class.

        The 'from_field' tells where we are coming from - we need this to
        determine if the objects are in fact to be deleted. Allow also
        skipping parent -> child -> parent chain preventing fast delete of
        the child.
        """
        if self.force_collection:
            return False
        if from_field and from_field.remote_field.on_delete is not CASCADE:
            return False
        if hasattr(objs, "_meta"):
            model = objs._meta.model
        elif hasattr(objs, "model") and hasattr(objs, "_raw_delete"):
            model = objs.model
        else:
            return False
        if self._has_signal_listeners(model):
            return False
        # The use of from_field comes from the need to avoid cascade back to
        # parent when parent delete is cascading to child.
        opts = model._meta
        return (
            all(
                link == from_field
                for link in opts.concrete_model._meta.parents.values()
            )
            and
            # Foreign keys pointing to this model.
            all(
                related.field.remote_field.on_delete in SKIP_COLLECTION
                for related in get_candidate_relations_to_delete(opts)
            )
            and (
                # Something like generic foreign key.
                not any(
                    hasattr(field, "bulk_related_objects")
                    for field in opts.private_fields
                )
            )
        )