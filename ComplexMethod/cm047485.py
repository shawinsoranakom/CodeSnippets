def __get__(self, record: BaseModel, owner=None) -> T:
        """ return the value of field ``self`` on ``record`` """
        if record is None:
            return self         # the field is accessed through the owner class

        env = record.env
        if not (env.su or record._has_field_access(self, 'read')):
            # optimization: we called _has_field_access() to avoid an extra
            # function call in _check_field_access()
            record._check_field_access(self, 'read')

        record_len = len(record._ids)
        if record_len != 1:
            if record_len:
                # let ensure_one() raise the proper exception
                record.ensure_one()
                assert False, "unreachable"
            # null record -> return the null value for this field
            value = self.convert_to_cache(False, record, validate=False)
            return self.convert_to_record(value, record)

        if self.compute and self.store:
            # process pending computations
            self.recompute(record)

        record_id = record._ids[0]
        field_cache = self._get_cache(env)
        try:
            value = field_cache[record_id]
            # convert to record may also throw a KeyError if the value is not
            # in cache, in that case, the fallbacks should be implemented to
            # read it correctly
            return self.convert_to_record(value, record)
        except KeyError:
            pass
        # behavior in case of cache miss:
        #
        #   on a real record:
        #       stored -> fetch from database (computation done above)
        #       not stored and computed -> compute
        #       not stored and not computed -> default
        #
        #   on a new record w/ origin:
        #       stored and not (computed and readonly) -> fetch from origin
        #       stored and computed and readonly -> compute
        #       not stored and computed -> compute
        #       not stored and not computed -> default
        #
        #   on a new record w/o origin:
        #       stored and computed -> compute
        #       stored and not computed -> new delegate or default
        #       not stored and computed -> compute
        #       not stored and not computed -> default
        #
        if self.store and record_id:
            # real record: fetch from database
            recs = self._to_prefetch(record)
            try:
                recs._fetch_field(self)
                fallback_single = False
            except AccessError:
                if len(recs) == 1:
                    raise
                fallback_single = True
            if fallback_single:
                record._fetch_field(self)
            value = field_cache.get(record_id, SENTINEL)
            if value is SENTINEL:
                raise MissingError("\n".join([
                    env._("Record does not exist or has been deleted."),
                    env._("(Record: %(record)s, User: %(user)s)", record=record, user=env.uid),
                ])) from None

        elif self.store and record._origin and not (self.compute and self.readonly):
            # new record with origin: fetch from origin, and assign the
            # records to prefetch in cache (which is necessary for
            # relational fields to "map" prefetching ids to their value)
            recs = self._to_prefetch(record)
            try:
                for rec in recs:
                    if (rec_origin := rec._origin):
                        value = self.convert_to_cache(rec_origin[self.name], rec, validate=False)
                        self._update_cache(rec, value)
                fallback_single = False
            except (AccessError, KeyError, MissingError):
                if len(recs) == 1:
                    raise
                fallback_single = True
            if fallback_single:
                value = self.convert_to_cache(record._origin[self.name], record, validate=False)
                self._update_cache(record, value)
            # get the final value (see patches in x2many fields)
            value = field_cache[record_id]

        elif self.compute:
            # non-stored field or new record without origin: compute
            if env.is_protected(self, record):
                value = self.convert_to_cache(False, record, validate=False)
                self._update_cache(record, value)
            else:
                recs = record if self.recursive else self._to_prefetch(record)
                try:
                    self.compute_value(recs)
                    fallback_single = False
                except (AccessError, MissingError):
                    fallback_single = True
                if fallback_single:
                    self.compute_value(record)
                    recs = record

                missing_recs_ids = tuple(self._cache_missing_ids(recs))
                if missing_recs_ids:
                    missing_recs = record.browse(missing_recs_ids)
                    if self.readonly and not self.store:
                        raise ValueError(f"Compute method failed to assign {missing_recs}.{self.name}")
                    # fallback to null value if compute gives nothing, do it for every unset record
                    false_value = self.convert_to_cache(False, record, validate=False)
                    self._update_cache(missing_recs, false_value)

                # cache could have been entirely invalidated by compute
                # as some compute methods call indirectly env.invalidate_all()
                field_cache = self._get_cache(env)
                value = field_cache[record_id]

        elif self.type == 'many2one' and self.delegate and not record_id:
            # parent record of a new record: new record, with the same
            # values as record for the corresponding inherited fields
            def is_inherited_field(name):
                field = record._fields[name]
                return field.inherited and field.related.split('.')[0] == self.name

            parent = record.env[self.comodel_name].new({
                name: value
                for name, value in record._cache.items()
                if is_inherited_field(name)
            })
            # in case the delegate field has inverse one2many fields, this
            # updates the inverse fields as well
            value = self.convert_to_cache(parent, record, validate=False)
            self._update_cache(record, value)
            # set inverse fields on new records in the comodel
            # TODO move this logic to _update_cache?
            if inv_recs := parent.filtered(lambda r: not r.id):
                for invf in env.registry.field_inverses[self]:
                    invf._update_inverse(inv_recs, record)

        else:
            # non-stored field or stored field on new record: default value
            value = self.convert_to_cache(False, record, validate=False)
            self._update_cache(record, value)
            defaults = record.default_get([self.name])
            if self.name in defaults:
                # The null value above is necessary to convert x2many field
                # values. For instance, converting [(Command.LINK, id)]
                # accesses the field's current value, then adds the given
                # id. Without an initial value, the conversion ends up here
                # to determine the field's value, and generates an infinite
                # recursion.
                value = self.convert_to_cache(defaults[self.name], record)
                self._update_cache(record, value)
            # get the final value (see patches in x2many fields)
            value = field_cache[record_id]

        return self.convert_to_record(value, record)