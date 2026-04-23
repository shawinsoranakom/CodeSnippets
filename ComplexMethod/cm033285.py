def save_or_replace_latest(cls, user_canvas_id, dsl, title=None, description=None, release=None):
        """
        Persist a canvas snapshot into version history.

        If the latest version has the same DSL content, update that version in place
        instead of creating a new row.

        Exception: If the latest version is released (release=True) and current save is not,
        create a new version to protect the released version.
        """
        try:
            normalized_dsl = cls._normalize_dsl(dsl)
            latest = (
                cls.model.select()
                .where(cls.model.user_canvas_id == user_canvas_id)
                .order_by(cls.model.create_time.desc())
                .first()
            )

            # Repeated saves with the same DSL only refresh the latest snapshot.
            if latest and cls._normalize_dsl(latest.dsl) == normalized_dsl:
                # Protect released version: if latest is released and current is not,
                # create a new version instead of updating
                if latest.release and not release:
                    insert_data = {"user_canvas_id": user_canvas_id, "dsl": normalized_dsl}
                    if title is not None:
                        insert_data["title"] = title
                    if description is not None:
                        insert_data["description"] = description
                    if release is not None:
                        insert_data["release"] = release
                    cls.insert(**insert_data)
                    cls.delete_all_versions(user_canvas_id)
                    return None, True

                # Normal case: update existing version
                # DSL unchanged: do NOT update title to preserve version identity
                # Only update dsl (for normalization consistency), description, and release
                update_data = {"dsl": normalized_dsl}
                if description is not None:
                    update_data["description"] = description
                if release is not None:
                    update_data["release"] = release
                cls.update_by_id(latest.id, update_data)
                cls.delete_all_versions(user_canvas_id)
                return latest.id, False

            # Real content changes create a new snapshot.
            insert_data = {"user_canvas_id": user_canvas_id, "dsl": normalized_dsl}
            if title is not None:
                insert_data["title"] = title
            if description is not None:
                insert_data["description"] = description
            if release is not None:
                insert_data["release"] = release
            cls.insert(**insert_data)
            cls.delete_all_versions(user_canvas_id)
            return None, True
        except Exception as e:
            logging.exception(e)
            return None, None