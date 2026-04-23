def test_execution_coordination_simulation(self, redis_client):
        """Simulate graph execution coordination across multiple pods."""
        graph_exec_id = str(uuid.uuid4())
        lock_key = f"execution:{graph_exec_id}"

        # Simulate 3 pods trying to execute same graph
        pods = [f"pod_{i}" for i in range(3)]
        execution_results = {}

        def execute_graph(pod_id):
            """Simulate graph execution with cluster lock."""
            lock = ClusterLock(redis_client, lock_key, pod_id, timeout=300)

            if lock.try_acquire() == pod_id:
                # Simulate execution work
                execution_results[pod_id] = "executed"
                time.sleep(0.1)
                lock.release()
            else:
                execution_results[pod_id] = "rejected"

        threads = []
        for pod_id in pods:
            thread = Thread(target=execute_graph, args=(pod_id,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Only one pod should have executed
        executed_count = sum(
            1 for result in execution_results.values() if result == "executed"
        )
        rejected_count = sum(
            1 for result in execution_results.values() if result == "rejected"
        )

        assert executed_count == 1
        assert rejected_count == 2