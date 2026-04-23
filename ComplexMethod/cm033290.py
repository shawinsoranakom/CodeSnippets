def get_list(cls, dialog_id, tenant_id,
                 page_number, items_per_page,
                 orderby, desc, id=None, user_id=None, include_dsl=True, keywords="",
                 from_date=None, to_date=None, exp_user_id=None
                 ):
        if include_dsl:
            sessions = cls.model.select().where(cls.model.dialog_id == dialog_id)
        else:
            fields = [field for field in cls.model._meta.fields.values() if field.name != 'dsl']
            sessions = cls.model.select(*fields).where(cls.model.dialog_id == dialog_id)
        if id:
            sessions = sessions.where(cls.model.id == id)
        if user_id:
            sessions = sessions.where(cls.model.user_id == user_id)
        if keywords:
            sessions = sessions.where(peewee.fn.LOWER(cls.model.message).contains(keywords.lower()))
        if from_date:
            sessions = sessions.where(cls.model.create_date >= from_date)
        if to_date:
            sessions = sessions.where(cls.model.create_date <= to_date)
        if exp_user_id:
            sessions = sessions.where(cls.model.exp_user_id == exp_user_id)
        if desc:
            sessions = sessions.order_by(cls.model.getter_by(orderby).desc())
        else:
            sessions = sessions.order_by(cls.model.getter_by(orderby).asc())
        count = sessions.count()
        sessions = sessions.paginate(page_number, items_per_page)

        return count, list(sessions.dicts())