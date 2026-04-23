async def _cleanup_resources(self) -> None:
        clients = await self.service._get_provider_clients(user_id=self.user_id, db=self.db)  # noqa: SLF001
        print("\nCleanup Resources")
        print("-" * 90)
        print(
            f"cleanup targets: deployments={len(self.created_deployment_ids)} "
            f"snapshots={len(self.created_snapshot_ids)} "
            f"configs={len(self.created_config_ids)}"
        )

        deleted_deployments = 0
        deleted_snapshots = 0
        deleted_configs = 0

        for deployment_id in sorted(self.created_deployment_ids):
            print(f"[cleanup] deleting deployment {deployment_id}...")
            with suppress(Exception):
                await self.service.delete(user_id=self.user_id, deployment_id=deployment_id, db=self.db)
                deleted_deployments += 1
                print(f"[cleanup] deleted deployment {deployment_id}")

        for snapshot_id in sorted(self.created_snapshot_ids):
            print(f"[cleanup] deleting snapshot {snapshot_id}...")
            try:
                await asyncio.to_thread(clients.tool.delete, snapshot_id)
                deleted_snapshots += 1
                print(f"[cleanup] deleted snapshot {snapshot_id}")
            except ClientAPIException as exc:
                if exc.response.status_code != HTTP_STATUS_NOT_FOUND:
                    print(f"[cleanup-warning] snapshot {snapshot_id}: {exc}")
                else:
                    print(f"[cleanup] snapshot {snapshot_id} already deleted (404)")

        for config_id in sorted(self.created_config_ids):
            print(f"[cleanup] deleting config {config_id}...")
            try:
                await asyncio.to_thread(clients.connections.delete, config_id)
                deleted_configs += 1
                print(f"[cleanup] deleted config {config_id}")
            except ClientAPIException as exc:
                if exc.response.status_code != HTTP_STATUS_NOT_FOUND:
                    print(f"[cleanup-warning] config {config_id}: {exc}")
                else:
                    print(f"[cleanup] config {config_id} already deleted (404)")

        print(
            f"cleanup completed: deployments_deleted={deleted_deployments} "
            f"snapshots_deleted={deleted_snapshots} "
            f"configs_deleted={deleted_configs}"
        )
        print("-" * 90)