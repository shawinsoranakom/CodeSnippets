def test_retrieve_function(self, agent_memory):
        focus_points = ["who i love?"]
        retrieved = dict()
        for focal_pt in focus_points:
            nodes = [
                [i.last_accessed, i]
                for i in agent_memory.event_list + agent_memory.thought_list
                if "idle" not in i.embedding_key
            ]
            nodes = sorted(nodes, key=lambda x: x[0])
            nodes = [i for created, i in nodes]
            results = agent_retrieve(agent_memory, datetime.now() - timedelta(days=120), 0.99, focal_pt, nodes, 5)
            final_result = []
            for n in results:
                for i in agent_memory.storage:
                    if i.memory_id == n:
                        i.last_accessed = datetime.now() - timedelta(days=120)
                        final_result.append(i)

            retrieved[focal_pt] = final_result
        logger.info(f"检索结果为{retrieved}")