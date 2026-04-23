def apply_to_cmd(self, cmd: list[str]) -> list[str]:
        cmd = list(cmd)

        for k, v in self.items():
            # Skip the '_benchmark_name' field, not a parameter
            if k == "_benchmark_name":
                continue

            # Serialize dict values as JSON
            if isinstance(v, dict):
                v = json.dumps(v)

            for k_candidate in self._iter_cmd_key_candidates(k):
                try:
                    k_idx = cmd.index(k_candidate)

                    # Replace existing parameter
                    normalized = self._normalize_cmd_kv_pair(k, v)
                    if len(normalized) == 1:
                        # Boolean flag
                        cmd[k_idx] = normalized[0]
                    else:
                        # Key-value pair
                        cmd[k_idx] = normalized[0]
                        cmd[k_idx + 1] = normalized[1]

                    break
                except ValueError:
                    continue
            else:
                # Add new parameter
                cmd.extend(self._normalize_cmd_kv_pair(k, v))

        return cmd