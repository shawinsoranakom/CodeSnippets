def _log_activity_get_documents(self, orig_obj_changes, stream_field, stream, groupby_method=False):
        """ Generic method to log activity. To use with
        _log_activity method. It either log on uppermost
        ongoing documents or following documents. This method
        find all the documents and responsible for which a note
        has to be log. It also generate a rendering_context in
        order to render a specific note by documents containing
        only the information relative to the document it. For example
        we don't want to notify a picking on move that it doesn't
        contain.

        :param dict orig_obj_changes: contain a record as key and the
            change on this record as value.
            eg: {'move_id': (new product_uom_qty, old product_uom_qty)}
        :param str stream_field: It has to be a field of the
            records that are register in the key of 'orig_obj_changes'
            eg: 'move_dest_ids' if we use move as record (previous example)
                - 'UP' if we want to log on the upper most ongoing
                documents.
                - 'DOWN' if we want to log on following documents.
        :param str stream: ``'UP'`` or ``'DOWN'``
        :param groupby_method: Only need when
            stream is 'DOWN', it should group by tuple(object on
            which the activity is log, the responsible for this object)
        """
        if self.env.context.get('skip_activity'):
            return {}
        move_to_orig_object_rel = {co: ooc for ooc in orig_obj_changes.keys() for co in ooc[stream_field]}
        origin_objects = self.env[list(orig_obj_changes.keys())[0]._name].concat(*list(orig_obj_changes.keys()))
        # The purpose here is to group each destination object by
        # (document to log, responsible) no matter the stream direction.
        # example:
        # {'(delivery_picking_1, admin)': stock.move(1, 2)
        #  '(delivery_picking_2, admin)': stock.move(3)}
        visited_documents = {}
        if stream == 'DOWN':
            if groupby_method:
                grouped_moves = groupby(origin_objects.mapped(stream_field), key=groupby_method)
            else:
                raise AssertionError('You have to define a groupby method and pass them as arguments.')
        elif stream == 'UP':
            # When using upstream document it is required to define
            # _get_upstream_documents_and_responsibles on
            # destination objects in order to ascend documents.
            grouped_moves = {}
            for visited_move in origin_objects.mapped(stream_field):
                for document, responsible, visited in visited_move._get_upstream_documents_and_responsibles(self.env[visited_move._name]):
                    if grouped_moves.get((document, responsible)):
                        grouped_moves[(document, responsible)] |= visited_move
                        visited_documents[(document, responsible)] |= visited
                    else:
                        grouped_moves[(document, responsible)] = visited_move
                        visited_documents[(document, responsible)] = visited
            grouped_moves = grouped_moves.items()
        else:
            raise AssertionError('Unknown stream.')

        documents = {}
        for (parent, responsible), moves in grouped_moves:
            if not parent:
                continue
            moves = self.env[moves[0]._name].concat(*moves)
            # Get the note
            rendering_context = {move: (orig_object, orig_obj_changes[orig_object]) for move in moves for orig_object in move_to_orig_object_rel[move]}
            if visited_documents:
                documents[(parent, responsible)] = rendering_context, visited_documents.values()
            else:
                documents[(parent, responsible)] = rendering_context
        return documents