def update(self, other):
            assert other.cnt == 1
            self.cnt += other.cnt
            observation = other.observation
            new_backpointers = np.empty(graph.number_of_nodes(), dtype=int)

            reachable_nodes = defaultdict(list)
            new_ppb = np.full(graph.number_of_nodes(), -np.inf)

            for start_idx in self.trimmed_nodes_idx:
                start_node = idx_to_node[start_idx]
                start_node_cost = self.ppb[start_idx]
                for node in graph.successors(start_node):
                    log_transition_ppb = graph.get_edge_data(start_node, node)[
                        "log_transition_ppb"
                    ]
                    reachable_nodes[node].append(
                        (start_node_cost + log_transition_ppb, start_idx)
                    )
            trimmed_nodes_idx = []
            for node, candidates in reachable_nodes.items():
                node_emission_log_prob = graph.nodes[node]["calc_emission_log_ppb"](
                    observation
                )
                # if _hacky_speedups and node_emission_log_prob < -10000:
                # continue
                assert len(candidates) > 0, f"{node=}"
                max_ppb, max_idx = max(candidates)
                idx = graph.nodes[node]["idx"]
                new_ppb[idx] = node_emission_log_prob + max_ppb
                new_backpointers[idx] = max_idx
                trimmed_nodes_idx.append(idx)

            if len(trimmed_nodes_idx) > self.beam_size:
                trimmed_costs = new_ppb[trimmed_nodes_idx]
                sel = np.argpartition(
                    trimmed_costs, trimmed_costs.shape[0] - self.beam_size
                )
                trimmed_nodes_idx = [
                    trimmed_nodes_idx[s] for s in sel[-self.beam_size :]
                ]
            self.trimmed_nodes_idx = trimmed_nodes_idx
            self.backpointers.append(new_backpointers)
            best_final_state_idx = int(new_ppb.argmax())
            self.ppb = new_ppb
            path_idx = [best_final_state_idx]
            if (
                num_results_kept is not None
                and len(self.backpointers) >= num_results_kept
            ):
                self.backpointers.popleft()
            for backpointers in reversed(self.backpointers):
                path_idx.append(backpointers[path_idx[-1]])
            self.path_states = tuple(reversed([idx_to_node[x] for x in path_idx]))