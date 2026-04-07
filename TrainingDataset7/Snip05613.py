def register(cls, test, list_filter_class, take_priority=False):
        if take_priority:
            # This is to allow overriding the default filters for certain types
            # of fields with some custom filters. The first found in the list
            # is used in priority.
            cls._field_list_filters.insert(
                cls._take_priority_index, (test, list_filter_class)
            )
            cls._take_priority_index += 1
        else:
            cls._field_list_filters.append((test, list_filter_class))