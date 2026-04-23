def get_by_tenant_ids(cls, joined_tenant_ids, user_id,
                          page_number, items_per_page,
                          orderby, desc, keywords, canvas_category=None
                          ):
        fields = [
            cls.model.id,
            cls.model.avatar,
            cls.model.title,
            cls.model.description,
            cls.model.permission,
            cls.model.user_id.alias("tenant_id"),
            User.nickname,
            User.avatar.alias('tenant_avatar'),
            cls.model.update_time,
            cls.model.canvas_category,
        ]
        if keywords:
            agents = cls.model.select(*fields).join(User, on=(cls.model.user_id == User.id)).where(
                (((cls.model.user_id.in_(joined_tenant_ids)) & (cls.model.permission == TenantPermission.TEAM.value)) | (cls.model.user_id == user_id)),
                (fn.LOWER(cls.model.title).contains(keywords.lower()))
            )
        else:
            agents = cls.model.select(*fields).join(User, on=(cls.model.user_id == User.id)).where(
                (((cls.model.user_id.in_(joined_tenant_ids)) & (cls.model.permission == TenantPermission.TEAM.value)) | (cls.model.user_id == user_id))
            )
        if canvas_category:
            agents = agents.where(cls.model.canvas_category == canvas_category)
        if desc:
            agents = agents.order_by(cls.model.getter_by(orderby).desc())
        else:
            agents = agents.order_by(cls.model.getter_by(orderby).asc())

        count = agents.count()
        if page_number and items_per_page:
            agents = agents.paginate(page_number, items_per_page)

        agents_list = list(agents.dicts())

        # Get latest release time for each canvas
        if agents_list:
            canvas_ids = [a['id'] for a in agents_list]
            release_times = (
                UserCanvasVersion.select(UserCanvasVersion.user_canvas_id, fn.MAX(UserCanvasVersion.create_time).alias("release_time"))
                .where((UserCanvasVersion.user_canvas_id.in_(canvas_ids)) & (UserCanvasVersion.release))
                .group_by(UserCanvasVersion.user_canvas_id)
            )
            release_time_map = {r.user_canvas_id: r.release_time for r in release_times}

            for agent in agents_list:
                agent['release_time'] = release_time_map.get(agent['id'])

        return agents_list, count