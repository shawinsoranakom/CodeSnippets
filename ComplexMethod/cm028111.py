def __init__(self,
               num_clones=1,
               clone_on_cpu=False,
               replica_id=0,
               num_replicas=1,
               num_ps_tasks=0,
               worker_job_name='worker',
               ps_job_name='ps'):
    """Create a DeploymentConfig.

    The config describes how to deploy a model across multiple clones and
    replicas.  The model will be replicated `num_clones` times in each replica.
    If `clone_on_cpu` is True, each clone will placed on CPU.

    If `num_replicas` is 1, the model is deployed via a single process.  In that
    case `worker_device`, `num_ps_tasks`, and `ps_device` are ignored.

    If `num_replicas` is greater than 1, then `worker_device` and `ps_device`
    must specify TensorFlow devices for the `worker` and `ps` jobs and
    `num_ps_tasks` must be positive.

    Args:
      num_clones: Number of model clones to deploy in each replica.
      clone_on_cpu: If True clones would be placed on CPU.
      replica_id: Integer.  Index of the replica for which the model is
        deployed.  Usually 0 for the chief replica.
      num_replicas: Number of replicas to use.
      num_ps_tasks: Number of tasks for the `ps` job. 0 to not use replicas.
      worker_job_name: A name for the worker job.
      ps_job_name: A name for the parameter server job.

    Raises:
      ValueError: If the arguments are invalid.
    """
    if num_replicas > 1:
      if num_ps_tasks < 1:
        raise ValueError('When using replicas num_ps_tasks must be positive')
    if num_replicas > 1 or num_ps_tasks > 0:
      if not worker_job_name:
        raise ValueError('Must specify worker_job_name when using replicas')
      if not ps_job_name:
        raise ValueError('Must specify ps_job_name when using parameter server')
    if replica_id >= num_replicas:
      raise ValueError('replica_id must be less than num_replicas')
    self._num_clones = num_clones
    self._clone_on_cpu = clone_on_cpu
    self._replica_id = replica_id
    self._num_replicas = num_replicas
    self._num_ps_tasks = num_ps_tasks
    self._ps_device = '/job:' + ps_job_name if num_ps_tasks > 0 else ''
    self._worker_device = '/job:' + worker_job_name if num_ps_tasks > 0 else ''