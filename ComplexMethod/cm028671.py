def get_distribution_strategy(distribution_strategy="mirrored",
                              num_gpus=0,
                              all_reduce_alg=None,
                              num_packs=1,
                              tpu_address=None,
                              **kwargs):
  """Return a Strategy for running the model.

  Args:
    distribution_strategy: a string specifying which distribution strategy to
      use. Accepted values are "off", "one_device", "mirrored",
      "parameter_server", "multi_worker_mirrored", and "tpu" -- case
      insensitive. "tpu" means to use TPUStrategy using `tpu_address`.
      "off" means to use the default strategy which is obtained from
      tf.distribute.get_strategy (for details on the default strategy, see
      https://www.tensorflow.org/guide/distributed_training#default_strategy).
    num_gpus: Number of GPUs to run this model.
    all_reduce_alg: Optional. Specifies which algorithm to use when performing
      all-reduce. For `MirroredStrategy`, valid values are "nccl" and
      "hierarchical_copy". For `MultiWorkerMirroredStrategy`, valid values are
      "ring" and "nccl".  If None, DistributionStrategy will choose based on
      device topology.
    num_packs: Optional.  Sets the `num_packs` in `tf.distribute.NcclAllReduce`
      or `tf.distribute.HierarchicalCopyAllReduce` for `MirroredStrategy`.
    tpu_address: Optional. String that represents TPU to connect to. Must not be
      None if `distribution_strategy` is set to `tpu`.
    **kwargs: Additional kwargs for internal usages.

  Returns:
    tf.distribute.Strategy object.
  Raises:
    ValueError: if `distribution_strategy` is "off" or "one_device" and
      `num_gpus` is larger than 1; or `num_gpus` is negative or if
      `distribution_strategy` is `tpu` but `tpu_address` is not specified.
  """
  del kwargs
  if num_gpus < 0:
    raise ValueError("`num_gpus` can not be negative.")

  if not isinstance(distribution_strategy, str):
    msg = ("distribution_strategy must be a string but got: %s." %
           (distribution_strategy,))
    if distribution_strategy == False:  # pylint: disable=singleton-comparison,g-explicit-bool-comparison
      msg += (" If you meant to pass the string 'off', make sure you add "
              "quotes around 'off' so that yaml interprets it as a string "
              "instead of a bool.")
    raise ValueError(msg)

  distribution_strategy = distribution_strategy.lower()
  if distribution_strategy == "off":
    if num_gpus > 1:
      raise ValueError(f"When {num_gpus} GPUs are specified, "
                       "distribution_strategy flag cannot be set to `off`.")
    # Return the default distribution strategy.
    return tf.distribute.get_strategy()

  if distribution_strategy == "tpu":
    # When tpu_address is an empty string, we communicate with local TPUs.
    # Bug workaround that in v5p we need to explicitly specify the device
    # assignment when using tpu strategy, adding device assignment to the
    # strategy.
    cluster_resolver = tf.distribute.cluster_resolver.TPUClusterResolver(
        tpu=tpu_address
    )
    if tpu_address not in ("", "local"):
      tf.config.experimental_connect_to_cluster(cluster_resolver)
    topology = tf.tpu.experimental.initialize_tpu_system(cluster_resolver)

    device_assignment = None
    if hasattr(tf.tpu.experimental, "HardWareFeature"):
      hardware_feature = tf.tpu.experimental.HardWareFeature(
          cluster_resolver.tpu_hardware_feature
      )
      if (
          hardware_feature.embedding_feature
          == tf.tpu.experimental.HardwareFeature.EmbeddingFeature.V2
      ):
        tpu_metadata = cluster_resolver.get_tpu_system_metadata()
        device_assignment = tf.tpu.experimental.DeviceAssignment.build(
            topology, num_replicas=tpu_metadata.num_cores
        )

    return tf.distribute.TPUStrategy(
        cluster_resolver, experimental_device_assignment=device_assignment)

  if distribution_strategy == "multi_worker_mirrored":
    return tf.distribute.experimental.MultiWorkerMirroredStrategy(
        communication=_collective_communication(all_reduce_alg))

  if distribution_strategy == "one_device":
    if num_gpus == 0:
      return tf.distribute.OneDeviceStrategy("device:CPU:0")
    if num_gpus > 1:
      raise ValueError("`OneDeviceStrategy` can not be used for more than "
                       "one device.")
    return tf.distribute.OneDeviceStrategy("device:GPU:0")

  if distribution_strategy == "mirrored":
    if num_gpus == 0:
      devices = ["device:CPU:0"]
    else:
      devices = ["device:GPU:%d" % i for i in range(num_gpus)]
    return tf.distribute.MirroredStrategy(
        devices=devices,
        cross_device_ops=_mirrored_cross_device_ops(all_reduce_alg, num_packs))

  if distribution_strategy == "parameter_server":
    cluster_resolver = tf.distribute.cluster_resolver.TFConfigClusterResolver()
    return tf.distribute.experimental.ParameterServerStrategy(cluster_resolver)

  raise ValueError("Unrecognized Distribution Strategy: %r" %
                   distribution_strategy)