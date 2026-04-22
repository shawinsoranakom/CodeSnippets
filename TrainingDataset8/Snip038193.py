def to_metric_str(self) -> str:
        return 'cache_memory_bytes{cache_type="%s",cache="%s"} %s' % (
            self.category_name,
            self.cache_name,
            self.byte_length,
        )