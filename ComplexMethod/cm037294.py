def get_metrics_snapshot() -> list[Metric]:
    """An API for accessing in-memory Prometheus metrics.

    Example:
        >>> for metric in llm.get_metrics():
        ...     if isinstance(metric, Counter):
        ...         print(f"{metric} = {metric.value}")
        ...     elif isinstance(metric, Gauge):
        ...         print(f"{metric} = {metric.value}")
        ...     elif isinstance(metric, Histogram):
        ...         print(f"{metric}")
        ...         print(f"    sum = {metric.sum}")
        ...         print(f"    count = {metric.count}")
        ...         for bucket_le, value in metrics.buckets.items():
        ...             print(f"    {bucket_le} = {value}")
    """
    collected: list[Metric] = []
    for metric in REGISTRY.collect():
        if not metric.name.startswith("vllm:"):
            continue
        if metric.type == "gauge":
            samples = _get_samples(metric)
            for s in samples:
                collected.append(
                    Gauge(name=metric.name, labels=s.labels, value=s.value)
                )
        elif metric.type == "counter":
            samples = _get_samples(metric, "_total")
            if metric.name == "vllm:spec_decode_num_accepted_tokens_per_pos":
                #
                # Ugly vllm:num_accepted_tokens_per_pos special case.
                #
                # This metric is a vector of counters - for each spec
                # decoding token position, we observe the number of
                # accepted tokens using a Counter labeled with 'position'.
                # We convert these into a vector of integer values.
                #
                for labels, values in _digest_num_accepted_by_pos_samples(samples):
                    collected.append(
                        Vector(name=metric.name, labels=labels, values=values)
                    )
            else:
                for s in samples:
                    collected.append(
                        Counter(name=metric.name, labels=s.labels, value=int(s.value))
                    )

        elif metric.type == "histogram":
            #
            # A histogram has a number of '_bucket' samples where
            # the 'le' label represents the upper limit of the bucket.
            # We convert these bucketized values into a dict of values
            # indexed by the value of the 'le' label. The 'le=+Inf'
            # label is a special case, catching all values observed.
            #
            bucket_samples = _get_samples(metric, "_bucket")
            count_samples = _get_samples(metric, "_count")
            sum_samples = _get_samples(metric, "_sum")
            for labels, buckets, count_value, sum_value in _digest_histogram(
                bucket_samples, count_samples, sum_samples
            ):
                collected.append(
                    Histogram(
                        name=metric.name,
                        labels=labels,
                        buckets=buckets,
                        count=count_value,
                        sum=sum_value,
                    )
                )
        else:
            raise AssertionError(f"Unknown metric type {metric.type}")

    return collected