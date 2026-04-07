def force_group_by(self):
        return ["GROUP BY TRUE"] if Database.sqlite_version_info < (3, 39) else []