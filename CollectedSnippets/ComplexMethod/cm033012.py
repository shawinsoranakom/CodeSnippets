def get_accessible_emails(
        self,
        workspace_id: str,
        project_ids: list[str] | None,
        team_id: str | None,
    ):

        ws_users = self.users_api.get_users(
            opts={
                "workspace": workspace_id,
                "opt_fields": "gid,name,email"
            }
        )

        workspace_users = {
            u["gid"]: u.get("email")
            for u in ws_users
            if u.get("email")
        }

        if not project_ids:
            return set(workspace_users.values())


        project_emails = set()

        for pid in project_ids:
            pid = pid.strip()
            if not pid:
                continue
            project = self.project_api.get_project(
                pid,
                opts={"opt_fields": "team,privacy_setting"}
            )

            if project.get("privacy_setting") == "private":
                if team_id and project.get("team", {}).get("gid") != team_id:
                    continue

            memberships = self.project_memberships_api.get_project_memberships_for_project(
                pid,
                opts={"opt_fields": "user.gid,user.email"}
            )

            for m in memberships:
                email = (m.get("user") or {}).get("email")
                if email:
                    project_emails.add(email)

        return project_emails