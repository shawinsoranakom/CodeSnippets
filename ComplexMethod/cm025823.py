def _update_issue_after_agent_upload(
        self,
        written_backup: WrittenBackup,
        agent_errors: dict[str, Exception],
        unavailable_agents: list[str],
    ) -> None:
        """Update issue registry after a backup is uploaded to agents."""

        addon_errors = written_backup.addon_errors
        failed_agents = unavailable_agents + [
            self.backup_agents[agent_id].name for agent_id in agent_errors
        ]
        folder_errors = written_backup.folder_errors

        if not failed_agents and not addon_errors and not folder_errors:
            # No issues to report, clear previous error
            ir.async_delete_issue(self.hass, DOMAIN, "automatic_backup_failed")
            return
        if failed_agents and not (addon_errors or folder_errors):
            # No issues with add-ons or folders, but issues with agents
            self._create_automatic_backup_failed_issue(
                "automatic_backup_failed_upload_agents",
                {"failed_agents": ", ".join(failed_agents)},
            )
        elif addon_errors and not (failed_agents or folder_errors):
            # No issues with agents or folders, but issues with add-ons
            self._create_automatic_backup_failed_issue(
                "automatic_backup_failed_addons",
                {
                    "failed_addons": ", ".join(
                        val.addon.name or val.addon.slug
                        for val in addon_errors.values()
                    )
                },
            )
        elif folder_errors and not (failed_agents or addon_errors):
            # No issues with agents or add-ons, but issues with folders
            self._create_automatic_backup_failed_issue(
                "automatic_backup_failed_folders",
                {"failed_folders": ", ".join(folder for folder in folder_errors)},
            )
        else:
            # Issues with agents, add-ons, and/or folders
            self._create_automatic_backup_failed_issue(
                "automatic_backup_failed_agents_addons_folders",
                {
                    "failed_agents": ", ".join(failed_agents) or "-",
                    "failed_addons": (
                        ", ".join(
                            val.addon.name or val.addon.slug
                            for val in addon_errors.values()
                        )
                        or "-"
                    ),
                    "failed_folders": ", ".join(f for f in folder_errors) or "-",
                },
            )