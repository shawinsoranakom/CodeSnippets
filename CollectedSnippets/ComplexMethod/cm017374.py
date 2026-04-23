def _get_fields(
        self,
        forward=True,
        reverse=True,
        include_parents=True,
        include_hidden=False,
        topmost_call=True,
    ):
        """
        Internal helper function to return fields of the model.
        * If forward=True, then fields defined on this model are returned.
        * If reverse=True, then relations pointing to this model are returned.
        * If include_hidden=True, then fields with is_hidden=True are returned.
        * The include_parents argument toggles if fields from parent models
          should be included. It has three values: True, False, and
          PROXY_PARENTS. When set to PROXY_PARENTS, the call will return all
          fields defined for the current model or any of its parents in the
          parent chain to the model's concrete model.
        """
        if include_parents not in (True, False, PROXY_PARENTS):
            raise TypeError(
                "Invalid argument for include_parents: %s" % (include_parents,)
            )
        # This helper function is used to allow recursion in ``get_fields()``
        # implementation and to provide a fast way for Django's internals to
        # access specific subsets of fields.

        # Creates a cache key composed of all arguments
        cache_key = (forward, reverse, include_parents, include_hidden, topmost_call)

        try:
            # In order to avoid list manipulation. Always return a shallow copy
            # of the results.
            return self._get_fields_cache[cache_key]
        except KeyError:
            pass

        fields = []
        # Recursively call _get_fields() on each parent, with the same
        # options provided in this call.
        if include_parents is not False:
            # In diamond inheritance it is possible that we see the same model
            # from two different routes. In that case, avoid adding fields from
            # the same parent again.
            parent_fields = set()
            for parent in self.parents:
                if (
                    parent._meta.concrete_model != self.concrete_model
                    and include_parents == PROXY_PARENTS
                ):
                    continue
                for obj in parent._meta._get_fields(
                    forward=forward,
                    reverse=reverse,
                    include_parents=include_parents,
                    include_hidden=include_hidden,
                    topmost_call=False,
                ):
                    if (
                        not getattr(obj, "parent_link", False)
                        or obj.model == self.concrete_model
                    ) and obj not in parent_fields:
                        fields.append(obj)
                        parent_fields.add(obj)

        if reverse and not self.proxy:
            # Tree is computed once and cached until the app cache is expired.
            # It is composed of a list of fields pointing to the current model
            # from other models.
            all_fields = self._relation_tree
            for field in all_fields:
                # If hidden fields should be included or the relation is not
                # intentionally hidden, add to the fields dict.
                if include_hidden or not field.remote_field.hidden:
                    fields.append(field.remote_field)

        if forward:
            fields += self.local_fields
            fields += self.local_many_to_many
            # Private fields are recopied to each child model, and they get a
            # different model as field.model in each child. Hence we have to
            # add the private fields separately from the topmost call. If we
            # did this recursively similar to local_fields, we would get field
            # instances with field.model != self.model.
            if topmost_call:
                fields += self.private_fields

        # In order to avoid list manipulation. Always
        # return a shallow copy of the results
        fields = make_immutable_fields_list("get_fields()", fields)

        # Store result into cache for later access
        self._get_fields_cache[cache_key] = fields
        return fields