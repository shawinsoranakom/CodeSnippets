def distribute_dataset(self, dataset):
        if not self._is_multi_process or not self.auto_shard_dataset:
            return dataset

        # Try to distribute a global tf.data.Dataset.
        from keras.src.utils.module_utils import tensorflow as tf

        if not tf.available or not isinstance(dataset, tf.data.Dataset):
            raise ValueError(
                "Only `tf.data.Dataset` is supported for auto-sharding, "
                f"got {type(dataset)}"
            )

        from tensorflow.python.data.experimental.ops import (
            distribute as tf_data_distribute,
        )

        global_batch_size = tf_data_distribute.compute_batch_size(dataset)
        if global_batch_size.numpy() < 0:
            raise ValueError(
                "The batch size of the input dataset is "
                "unknown. Please config the batch size for "
                "the input dataset, e.g via `dataset.batch(batch_size)`"
            )

        # We need to compute the per-process/worker/host batch size.
        # This will depend on how many model replicas we have on each process.
        # Note that this might be smaller than one if model replicas are sharded
        # across multiple processes.
        mesh_batch_dim_index = self.device_mesh.axis_names.index(
            self.batch_dim_name
        )
        num_model_replicas = self.device_mesh.shape[mesh_batch_dim_index]
        if num_model_replicas == 1:
            # No sharding is needed in this case. Each process will have the
            # global batch size, and data from the iterator will need to be
            # replicated across all processes.
            return dataset.prefetch(tf.data.AUTOTUNE)
        num_model_replicas_per_process = num_model_replicas / self._num_process
        if num_model_replicas_per_process >= 1:
            # Each process will have one or more full model replicas. Data will
            # be sharded across all processes without replication.
            if global_batch_size % self._num_process != 0:
                raise ValueError(
                    "Global batch size must be divisible by the number of "
                    f"processes. `global_batch_size`={global_batch_size} and "
                    f"`num_process`={self._num_process}"
                )
            per_process_batch_size = global_batch_size // self._num_process
            distributed_dataset = dataset.rebatch(per_process_batch_size)
            distributed_dataset = distributed_dataset.shard(
                num_shards=self._num_process,
                index=self._process_id,
            )
            return distributed_dataset.prefetch(tf.data.AUTOTUNE)
        else:
            # Model replicas are sharded across multiple processes. Data will be
            # sharded across model replicas, and replicated across processes
            # within the same model replica.
            if global_batch_size % num_model_replicas != 0:
                raise ValueError(
                    "Global batch size must be divisible by the number of "
                    f"replicas. `global_batch_size`={global_batch_size} and "
                    f"`num_model_replicas`={num_model_replicas}"
                )
            per_process_batch_size = global_batch_size // num_model_replicas
            distributed_dataset = dataset.rebatch(per_process_batch_size)
            processes_per_replica = self._num_process // num_model_replicas
            # Each process belongs to a replica group. Determine which replica
            # this process group belongs to.
            data_shard_id = self._process_id // processes_per_replica
            distributed_dataset = distributed_dataset.shard(
                num_shards=num_model_replicas,
                index=data_shard_id,
            )
            return distributed_dataset.prefetch(tf.data.AUTOTUNE)