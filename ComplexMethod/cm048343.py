def _to_store(self, store: Store, fields, **kwargs):
        super()._to_store(store, [f for f in fields if f != "record_rating"], **kwargs)
        if "record_rating" in fields:
            for records in self._records_by_model_name().values():
                if (
                    issubclass(self.pool[records._name], self.pool["rating.mixin"])
                    and records._has_field_access(records._fields["rating_avg"], 'read')
                ):
                    all_stats = {}
                    if records._allow_publish_rating_stats():
                        all_stats = records._rating_get_stats_per_record()
                    record_fields = [
                        "rating_avg",
                        "rating_count",
                        Store.Attr(
                            "rating_stats",
                            lambda record, all_stats=all_stats: all_stats.get(record.id),
                            predicate=lambda record: record._allow_publish_rating_stats(),
                        ),
                    ]
                    store.add(records, record_fields, as_thread=True)