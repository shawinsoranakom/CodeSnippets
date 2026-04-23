def __init__(self, record: BaseModel, view: None | int | str | BaseModel = None) -> None:
        assert isinstance(record, BaseModel)
        assert len(record) <= 1

        # use object.__setattr__ to bypass Form's override of __setattr__
        object.__setattr__(self, '_record', record)
        object.__setattr__(self, '_env', record.env)

        # determine view and process it
        if isinstance(view, BaseModel):
            assert view._name == 'ir.ui.view', "the view parameter must be a view id, xid or record, got %s" % view
            view_id = view.id
        elif isinstance(view, str):
            view_id = record.env.ref(view).id
        else:
            view_id = view or False

        views = record.get_views([(view_id, 'form')])
        object.__setattr__(self, '_models_info', views['models'])
        # self._models_info = {model_name: {fields: {field_name: field_info}}}
        tree = etree.fromstring(views['views']['form']['arch'])
        view = self._process_view(tree, record)
        object.__setattr__(self, '_view', view)
        # self._view = {
        #     'tree': view_arch_etree,
        #     'fields': {field_name: field_info},
        #     'fields_spec': web_read_fields_spec,
        #     'modifiers': {field_name: {modifier: expression}},
        #     'contexts': {field_name: field_context_str},
        #     'onchange': onchange_spec,
        # }

        # determine record values
        object.__setattr__(self, '_values', UpdateDict())
        if record:
            self._init_from_record()
        else:
            self._init_from_defaults()