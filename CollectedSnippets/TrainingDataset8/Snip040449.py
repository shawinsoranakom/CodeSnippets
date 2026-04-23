def cypress_flags(self) -> List[str]:
        """Flags to pass to Cypress"""
        flags = ["--config", f"integrationFolder={self.tests_dir}/specs"]
        if self.record_results:
            flags.append("--record")
        if self.update_snapshots:
            flags.extend(["--env", "updateSnapshots=true"])
        if self.cypress_env_vars:
            vars_str = ",".join(f"{k}={v}" for k, v in self.cypress_env_vars.items())
            flags.extend(["--env", vars_str])
        return flags