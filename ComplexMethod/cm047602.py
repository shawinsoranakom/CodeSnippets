def modified(self, fnames: Collection[str], create: bool = False, before: bool = False) -> None:
        """ Notify that fields will be or have been modified on ``self``. This
        invalidates the cache where necessary, and prepares the recomputation of
        dependent stored fields.

        :param fnames: iterable of field names modified on records ``self``
        :param create: whether called in the context of record creation
        :param before: whether called before modifying records ``self``
        """
        if not self or not fnames:
            return

        # The triggers of a field F is a tree that contains the fields that
        # depend on F, together with the fields to inverse to find out which
        # records to recompute.
        #
        # For instance, assume that G depends on F, H depends on X.F, I depends
        # on W.X.F, and J depends on Y.F. The triggers of F will be the tree:
        #
        #                              [G]
        #                            X/   \Y
        #                          [H]     [J]
        #                        W/
        #                      [I]
        #
        # This tree provides perfect support for the trigger mechanism:
        # when F is # modified on records,
        #  - mark G to recompute on records,
        #  - mark H to recompute on inverse(X, records),
        #  - mark I to recompute on inverse(W, inverse(X, records)),
        #  - mark J to recompute on inverse(Y, records).

        if before:
            # When called before modification, we should determine what
            # currently depends on self, and it should not be recomputed before
            # the modification.  So we only collect what should be marked for
            # recomputation.
            marked = self.env.transaction.tocompute     # {field: ids}
            tomark = defaultdict(OrderedSet)            # {field: ids}
        else:
            # When called after modification, one should traverse backwards
            # dependencies by taking into account all fields already known to
            # be recomputed.  In that case, we mark fieds to compute as soon as
            # possible.
            marked = {}
            tomark = self.env.transaction.tocompute

        # determine what to trigger (with iterators)
        todo = [self._modified([self._fields[fname] for fname in fnames], create)]

        # process what to trigger by lazily chaining todo
        for field, records, create in itertools.chain.from_iterable(todo):
            records -= self.env.protected(field)
            if not records:
                continue

            if field.recursive:
                # discard already processed records, in order to avoid cycles
                if field.compute and field.store:
                    ids = (marked.get(field) or set()) | (tomark.get(field) or set())
                    records = records.browse(id_ for id_ in records._ids if id_ not in ids)
                else:
                    # get only records that have a value in cache (in any context)
                    ids_in_cache = field._get_all_cache_ids(self.env)
                    records = records.browse(id_ for id_ in records._ids if id_ in ids_in_cache)
                if not records:
                    continue
                # recursively trigger recomputation of field's dependents
                todo.append(records._modified([field], create))

            # mark for recomputation (now or later, depending on 'before')
            if field.compute and field.store:
                tomark[field].update(records._ids)
            else:
                # Don't force the recomputation of compute fields which are
                # not stored as this is not really necessary.
                field._invalidate_cache(self.env, records._ids)

        if before:
            # effectively mark for recomputation now
            for field, ids in tomark.items():
                records = self.env[field.model_name].browse(ids)
                self.env.add_to_compute(field, records)