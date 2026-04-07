def create_forward_many_to_many_manager(superclass, rel, reverse):
    """
    Create a manager for the either side of a many-to-many relation.

    This manager subclasses another manager, generally the default manager of
    the related model, and adds behaviors specific to many-to-many relations.
    """

    class ManyRelatedManager(superclass, AltersData):
        def __init__(self, instance=None):
            super().__init__()

            self.instance = instance

            if not reverse:
                self.model = rel.model
                self.query_field_name = rel.field.related_query_name()
                self.prefetch_cache_name = rel.field.name
                self.source_field_name = rel.field.m2m_field_name()
                self.target_field_name = rel.field.m2m_reverse_field_name()
                self.symmetrical = rel.symmetrical
            else:
                self.model = rel.related_model
                self.query_field_name = rel.field.name
                self.prefetch_cache_name = rel.field.related_query_name()
                self.source_field_name = rel.field.m2m_reverse_field_name()
                self.target_field_name = rel.field.m2m_field_name()
                self.symmetrical = False

            self.through = rel.through
            self.reverse = reverse

            self.source_field = self.through._meta.get_field(self.source_field_name)
            self.target_field = self.through._meta.get_field(self.target_field_name)

            self.core_filters = {}
            self.pk_field_names = {}
            for lh_field, rh_field in self.source_field.related_fields:
                core_filter_key = "%s__%s" % (self.query_field_name, rh_field.name)
                self.core_filters[core_filter_key] = getattr(instance, rh_field.attname)
                self.pk_field_names[lh_field.name] = rh_field.name

            self.related_val = self.source_field.get_foreign_related_value(instance)
            if None in self.related_val:
                raise ValueError(
                    '"%r" needs to have a value for field "%s" before '
                    "this many-to-many relationship can be used."
                    % (instance, self.pk_field_names[self.source_field_name])
                )
            # Even if this relation is not to pk, we require still pk value.
            # The wish is that the instance has been already saved to DB,
            # although having a pk value isn't a guarantee of that.
            if not instance._is_pk_set():
                raise ValueError(
                    "%r instance needs to have a primary key value before "
                    "a many-to-many relationship can be used."
                    % instance.__class__.__name__
                )

        def __call__(self, *, manager):
            manager = getattr(self.model, manager)
            manager_class = create_forward_many_to_many_manager(
                manager.__class__, rel, reverse
            )
            return manager_class(instance=self.instance)

        do_not_call_in_templates = True

        def _build_remove_filters(self, removed_vals):
            filters = Q.create([(self.source_field_name, self.related_val)])
            # No need to add a subquery condition if removed_vals is a QuerySet
            # without filters.
            removed_vals_filters = (
                not isinstance(removed_vals, QuerySet) or removed_vals._has_filters()
            )
            if removed_vals_filters:
                filters &= Q.create([(f"{self.target_field_name}__in", removed_vals)])
            if self.symmetrical:
                symmetrical_filters = Q.create(
                    [(self.target_field_name, self.related_val)]
                )
                if removed_vals_filters:
                    symmetrical_filters &= Q.create(
                        [(f"{self.source_field_name}__in", removed_vals)]
                    )
                filters |= symmetrical_filters
            return filters

        def _apply_rel_filters(self, queryset):
            """
            Filter the queryset for the instance this manager is bound to.
            """
            with queryset._avoid_cloning():
                queryset._add_hints(instance=self.instance)
                if self._db:
                    queryset = queryset.using(self._db)
                queryset._fetch_mode = self.instance._state.fetch_mode
                queryset._defer_next_filter = True
                return queryset._next_is_sticky().filter(**self.core_filters)

        def get_prefetch_cache(self):
            # Walk up the ancestor-chain (if cached) to try and find a prefetch
            # in an ancestor.
            for instance, _ in _traverse_ancestors(rel.field.model, self.instance):
                try:
                    return instance._prefetched_objects_cache[self.prefetch_cache_name]
                except (AttributeError, KeyError):
                    pass
            return None

        def _remove_prefetched_objects(self):
            # Walk up the ancestor-chain (if cached) to try and find a prefetch
            # in an ancestor.
            for instance, _ in _traverse_ancestors(rel.field.model, self.instance):
                try:
                    instance._prefetched_objects_cache.pop(self.prefetch_cache_name)
                except (AttributeError, KeyError):
                    pass  # nothing to clear from cache

        def get_queryset(self):
            if (cache := self.get_prefetch_cache()) is not None:
                return cache
            else:
                queryset = super().get_queryset()
                return self._apply_rel_filters(queryset)

        def get_prefetch_querysets(self, instances, querysets=None):
            _cloning_disabled = False
            if querysets:
                if len(querysets) != 1:
                    raise ValueError(
                        "querysets argument of get_prefetch_querysets() should have a "
                        "length of 1."
                    )
                queryset = querysets[0]
            else:
                _cloning_disabled = True
                queryset = super().get_queryset()._disable_cloning()

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)
            queryset = _filter_prefetch_queryset(
                queryset, self.query_field_name, instances
            )

            # M2M: need to annotate the query in order to get the primary model
            # that the secondary model was actually related to. We know that
            # there will already be a join on the join table, so we can just
            # add the select.

            # For non-autocreated 'through' models, can't assume we are
            # dealing with PK values.
            fk = self.through._meta.get_field(self.source_field_name)
            join_table = fk.model._meta.db_table
            connection = connections[queryset.db]
            qn = connection.ops.quote_name
            queryset = queryset.extra(
                select={
                    "_prefetch_related_val_%s"
                    % f.attname: "%s.%s"
                    % (qn(join_table), qn(f.column))
                    for f in fk.local_related_fields
                }
            )
            # Restore subsequent cloning operations.
            if _cloning_disabled:
                queryset._enable_cloning()

            return (
                queryset,
                lambda result: tuple(
                    f.get_db_prep_value(
                        getattr(result, f"_prefetch_related_val_{f.attname}"),
                        connection,
                    )
                    for f in fk.local_related_fields
                ),
                lambda inst: tuple(
                    f.get_db_prep_value(getattr(inst, f.attname), connection)
                    for f in fk.foreign_related_fields
                ),
                False,
                self.prefetch_cache_name,
                False,
            )

        @property
        def constrained_target(self):
            # If the through relation's target field's foreign integrity is
            # enforced, the query can be performed solely against the through
            # table as the INNER JOIN'ing against target table is unnecessary.
            if not self.target_field.db_constraint:
                return None
            db = router.db_for_read(self.through, instance=self.instance)
            if not connections[db].features.supports_foreign_keys:
                return None
            hints = {"instance": self.instance}
            manager = self.through._base_manager.db_manager(db, hints=hints)
            filters = {self.source_field_name: self.related_val[0]}
            # Nullable target rows must be excluded as well as they would have
            # been filtered out from an INNER JOIN.
            if self.target_field.null:
                filters["%s__isnull" % self.target_field_name] = False
            return manager.filter(**filters)

        def exists(self):
            if (
                superclass is Manager
                and self.get_prefetch_cache() is None
                and (constrained_target := self.constrained_target) is not None
            ):
                return constrained_target.exists()
            else:
                return super().exists()

        def count(self):
            if (
                superclass is Manager
                and self.get_prefetch_cache() is None
                and (constrained_target := self.constrained_target) is not None
            ):
                return constrained_target.count()
            else:
                return super().count()

        def _add_base(self, *objs, through_defaults=None, using=None, raw=False):
            db = using or router.db_for_write(self.through, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                self._add_items(
                    self.source_field_name,
                    self.target_field_name,
                    *objs,
                    through_defaults=through_defaults,
                    using=db,
                    raw=raw,
                )
                # If this is a symmetrical m2m relation to self, add the mirror
                # entry in the m2m table.
                if self.symmetrical:
                    self._add_items(
                        self.target_field_name,
                        self.source_field_name,
                        *objs,
                        through_defaults=through_defaults,
                        using=db,
                        raw=raw,
                    )

        def add(self, *objs, through_defaults=None):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.through, instance=self.instance)
            self._add_base(*objs, through_defaults=through_defaults, using=db)

        add.alters_data = True

        async def aadd(self, *objs, through_defaults=None):
            return await sync_to_async(self.add)(
                *objs, through_defaults=through_defaults
            )

        aadd.alters_data = True

        def _remove_base(self, *objs, using=None, raw=False):
            db = using or router.db_for_write(self.through, instance=self.instance)
            self._remove_items(
                self.source_field_name, self.target_field_name, *objs, using=db, raw=raw
            )

        def remove(self, *objs):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.through, instance=self.instance)
            self._remove_base(*objs, using=db)

        remove.alters_data = True

        async def aremove(self, *objs):
            return await sync_to_async(self.remove)(*objs)

        aremove.alters_data = True

        def _clear_base(self, using=None, raw=False):
            db = using or router.db_for_write(self.through, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                signals.m2m_changed.send(
                    sender=self.through,
                    action="pre_clear",
                    instance=self.instance,
                    reverse=self.reverse,
                    model=self.model,
                    pk_set=None,
                    using=db,
                    raw=raw,
                )
                filters = self._build_remove_filters(super().get_queryset().using(db))
                self.through._default_manager.using(db).filter(filters).delete()

                signals.m2m_changed.send(
                    sender=self.through,
                    action="post_clear",
                    instance=self.instance,
                    reverse=self.reverse,
                    model=self.model,
                    pk_set=None,
                    using=db,
                    raw=raw,
                )

        def clear(self):
            self._remove_prefetched_objects()
            db = router.db_for_write(self.through, instance=self.instance)
            self._clear_base(using=db)

        clear.alters_data = True

        async def aclear(self):
            return await sync_to_async(self.clear)()

        aclear.alters_data = True

        def set_base(self, objs, *, clear=False, through_defaults=None, raw=False):
            # Force evaluation of `objs` in case it's a queryset whose value
            # could be affected by `manager.clear()`. Refs #19816.
            objs = tuple(objs)

            db = router.db_for_write(self.through, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                self._remove_prefetched_objects()
                if clear:
                    self._clear_base(using=db, raw=raw)
                    self._add_base(
                        *objs, through_defaults=through_defaults, using=db, raw=raw
                    )
                else:
                    old_ids = set(
                        self.using(db).values_list(
                            self.target_field.target_field.attname, flat=True
                        )
                    )

                    new_objs = []
                    for obj in objs:
                        fk_val = (
                            self.target_field.get_foreign_related_value(obj)[0]
                            if isinstance(obj, self.model)
                            else self.target_field.get_prep_value(obj)
                        )
                        if fk_val in old_ids:
                            old_ids.remove(fk_val)
                        else:
                            new_objs.append(obj)

                    self._remove_base(*old_ids, using=db, raw=raw)
                    self._add_base(
                        *new_objs, through_defaults=through_defaults, using=db, raw=raw
                    )

        def set(self, objs, *, clear=False, through_defaults=None):
            self.set_base(objs, clear=clear, through_defaults=through_defaults)

        set.alters_data = True

        async def aset(self, objs, *, clear=False, through_defaults=None):
            return await sync_to_async(self.set)(
                objs=objs, clear=clear, through_defaults=through_defaults
            )

        aset.alters_data = True

        def create(self, *, through_defaults=None, **kwargs):
            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            new_obj = super(ManyRelatedManager, self.db_manager(db)).create(**kwargs)
            self.add(new_obj, through_defaults=through_defaults)
            return new_obj

        create.alters_data = True

        async def acreate(self, *, through_defaults=None, **kwargs):
            return await sync_to_async(self.create)(
                through_defaults=through_defaults, **kwargs
            )

        acreate.alters_data = True

        def get_or_create(self, *, through_defaults=None, **kwargs):
            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            obj, created = super(ManyRelatedManager, self.db_manager(db)).get_or_create(
                **kwargs
            )
            # We only need to add() if created because if we got an object back
            # from get() then the relationship already exists.
            if created:
                self.add(obj, through_defaults=through_defaults)
            return obj, created

        get_or_create.alters_data = True

        async def aget_or_create(self, *, through_defaults=None, **kwargs):
            return await sync_to_async(self.get_or_create)(
                through_defaults=through_defaults, **kwargs
            )

        aget_or_create.alters_data = True

        def update_or_create(self, *, through_defaults=None, **kwargs):
            db = router.db_for_write(self.instance.__class__, instance=self.instance)
            obj, created = super(
                ManyRelatedManager, self.db_manager(db)
            ).update_or_create(**kwargs)
            # We only need to add() if created because if we got an object back
            # from get() then the relationship already exists.
            if created:
                self.add(obj, through_defaults=through_defaults)
            return obj, created

        update_or_create.alters_data = True

        async def aupdate_or_create(self, *, through_defaults=None, **kwargs):
            return await sync_to_async(self.update_or_create)(
                through_defaults=through_defaults, **kwargs
            )

        aupdate_or_create.alters_data = True

        def _get_target_ids(self, target_field_name, objs):
            """
            Return the set of ids of `objs` that the target field references.
            """
            from django.db.models import Model

            target_ids = set()
            target_field = self.through._meta.get_field(target_field_name)
            for obj in objs:
                if isinstance(obj, self.model):
                    if not router.allow_relation(obj, self.instance):
                        raise ValueError(
                            'Cannot add "%r": instance is on database "%s", '
                            'value is on database "%s"'
                            % (obj, self.instance._state.db, obj._state.db)
                        )
                    target_id = target_field.get_foreign_related_value(obj)[0]
                    if target_id is None:
                        raise ValueError(
                            'Cannot add "%r": the value for field "%s" is None'
                            % (obj, target_field_name)
                        )
                    target_ids.add(target_id)
                elif isinstance(obj, Model):
                    raise TypeError(
                        "'%s' instance expected, got %r"
                        % (self.model._meta.object_name, obj)
                    )
                else:
                    target_ids.add(target_field.get_prep_value(obj))
            return target_ids

        def _get_missing_target_ids(
            self, source_field_name, target_field_name, db, target_ids
        ):
            """
            Return the subset of ids of `objs` that aren't already assigned to
            this relationship.
            """
            vals = (
                self.through._default_manager.using(db)
                .values_list(target_field_name, flat=True)
                .filter(
                    **{
                        source_field_name: self.related_val[0],
                        "%s__in" % target_field_name: target_ids,
                    }
                )
            )
            return target_ids.difference(vals)

        def _get_add_plan(self, db, source_field_name):
            """
            Return a boolean triple of the way the add should be performed.

            The first element is whether or not bulk_create(ignore_conflicts)
            can be used, the second whether or not signals must be sent, and
            the third element is whether or not the immediate bulk insertion
            with conflicts ignored can be performed.
            """
            # Conflicts can be ignored when the intermediary model is
            # auto-created as the only possible collision is on the
            # (source_id, target_id) tuple. The same assertion doesn't hold for
            # user-defined intermediary models as they could have other fields
            # causing conflicts which must be surfaced.
            can_ignore_conflicts = (
                self.through._meta.auto_created is not False
                and connections[db].features.supports_ignore_conflicts
            )
            # Don't send the signal when inserting duplicate data row
            # for symmetrical reverse entries.
            must_send_signals = (
                self.reverse or source_field_name == self.source_field_name
            ) and (signals.m2m_changed.has_listeners(self.through))
            # Fast addition through bulk insertion can only be performed
            # if no m2m_changed listeners are connected for self.through
            # as they require the added set of ids to be provided via
            # pk_set.
            return (
                can_ignore_conflicts,
                must_send_signals,
                (can_ignore_conflicts and not must_send_signals),
            )

        def _add_items(
            self,
            source_field_name,
            target_field_name,
            *objs,
            through_defaults=None,
            using=None,
            raw=False,
        ):
            # source_field_name: the PK fieldname in join table for the source
            # object target_field_name: the PK fieldname in join table for the
            # target object *objs - objects to add. Either object instances, or
            # primary keys of object instances.
            if not objs:
                return

            through_defaults = dict(resolve_callables(through_defaults or {}))
            target_ids = self._get_target_ids(target_field_name, objs)
            db = using or router.db_for_write(self.through, instance=self.instance)
            can_ignore_conflicts, must_send_signals, can_fast_add = self._get_add_plan(
                db, source_field_name
            )
            if can_fast_add:
                self.through._default_manager.using(db).bulk_create(
                    [
                        self.through(
                            **{
                                "%s_id" % source_field_name: self.related_val[0],
                                "%s_id" % target_field_name: target_id,
                            }
                        )
                        for target_id in target_ids
                    ],
                    ignore_conflicts=True,
                )
                return

            missing_target_ids = self._get_missing_target_ids(
                source_field_name, target_field_name, db, target_ids
            )
            with transaction.atomic(using=db, savepoint=False):
                if must_send_signals:
                    signals.m2m_changed.send(
                        sender=self.through,
                        action="pre_add",
                        instance=self.instance,
                        reverse=self.reverse,
                        model=self.model,
                        pk_set=missing_target_ids,
                        using=db,
                        raw=raw,
                    )
                # Add the ones that aren't there already.
                self.through._default_manager.using(db).bulk_create(
                    [
                        self.through(
                            **through_defaults,
                            **{
                                "%s_id" % source_field_name: self.related_val[0],
                                "%s_id" % target_field_name: target_id,
                            },
                        )
                        for target_id in missing_target_ids
                    ],
                    ignore_conflicts=can_ignore_conflicts,
                )

                if must_send_signals:
                    signals.m2m_changed.send(
                        sender=self.through,
                        action="post_add",
                        instance=self.instance,
                        reverse=self.reverse,
                        model=self.model,
                        pk_set=missing_target_ids,
                        using=db,
                        raw=raw,
                    )

        def _remove_items(
            self, source_field_name, target_field_name, *objs, using=None, raw=False
        ):
            # source_field_name: the PK colname in join table for the source
            # object target_field_name: the PK colname in join table for the
            # target object *objs - objects to remove. Either object instances,
            # or primary keys of object instances.
            if not objs:
                return

            # Check that all the objects are of the right type
            old_ids = set()
            for obj in objs:
                if isinstance(obj, self.model):
                    fk_val = self.target_field.get_foreign_related_value(obj)[0]
                    old_ids.add(fk_val)
                else:
                    old_ids.add(obj)

            db = using or router.db_for_write(self.through, instance=self.instance)
            with transaction.atomic(using=db, savepoint=False):
                # Send a signal to the other end if need be.
                signals.m2m_changed.send(
                    sender=self.through,
                    action="pre_remove",
                    instance=self.instance,
                    reverse=self.reverse,
                    model=self.model,
                    pk_set=old_ids,
                    using=db,
                    raw=raw,
                )
                target_model_qs = super().get_queryset()
                if target_model_qs._has_filters():
                    old_vals = target_model_qs.using(db).filter(
                        **{"%s__in" % self.target_field.target_field.attname: old_ids}
                    )
                else:
                    old_vals = old_ids
                filters = self._build_remove_filters(old_vals)
                self.through._default_manager.using(db).filter(filters).delete()

                signals.m2m_changed.send(
                    sender=self.through,
                    action="post_remove",
                    instance=self.instance,
                    reverse=self.reverse,
                    model=self.model,
                    pk_set=old_ids,
                    using=db,
                    raw=raw,
                )

    return ManyRelatedManager