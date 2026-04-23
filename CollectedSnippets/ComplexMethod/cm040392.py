def _reduce(v):
        """Reduce a single `PerReplica` object."""
        if _collective_all_reduce_multi_worker(strategy):
            if reduction == "concat":
                return _multi_worker_concat(v, strategy)
            elif reduction == "sum":
                return strategy.reduce("SUM", v)
            elif reduction == "mean":
                return strategy.reduce("MEAN", v, axis=0)

        if not _is_per_replica_instance(v):
            return v
        elif reduction == "first":
            return strategy.experimental_local_results(v)[0]
        elif reduction == "concat":
            if _is_tpu_multi_host(strategy):
                return _tpu_multi_host_concat(v, strategy)
            else:
                return concat(strategy.experimental_local_results(v))
        elif reduction == "sum":
            return tf.reduce_sum(strategy.experimental_local_results(v))
        elif reduction == "mean":
            return tf.reduce_mean(
                strategy.experimental_local_results(v), axis=0
            )
        else:
            raise ValueError(
                "`reduction` must be one of "
                '"first", "concat", "mean", "sum", or "auto". '
                f"Received: reduction={reduction}."
            )