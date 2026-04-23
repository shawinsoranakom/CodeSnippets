def _check_access(self, operation: str) -> tuple | None:
        """ Determine the subset of ``self`` for which ``operation`` is allowed.
        A custom implementation is done on activities as this document has some
        access rules and is based on related document for activities that are
        not covered by those rules.

        Access on activities are the following :

          * read: access rule AND (assigned to user OR read rights on related documents);
          * write: access rule OR (``mail_post_access`` or write) rights on related documents);
          * create: access rule AND (``mail_post_access`` or write) right on related documents;
          * unlink: access rule OR (``mail_post_access`` or write) rights on related documents);
        """
        result = super()._check_access(operation)
        if not self:
            return result

        # determine activities on which to check the related document
        if operation == 'read':
            # check activities allowed by access rules
            activities = self - result[0] if result else self
            activities -= activities.sudo().filtered_domain([('user_id', '=', self.env.uid)])
        elif operation == 'create':
            # check activities allowed by access rules
            activities = self - result[0] if result else self
        else:
            assert operation in ('write', 'unlink'), f"Unexpected operation {operation!r}"
            # check access to the model, and check the forbidden records only
            if self.browse()._check_access(operation):
                return result
            activities = result[0] if result else self.browse()
            result = None

        if not activities:
            return result

        # now check access on related document of 'activities', and collect the
        # ids of forbidden activities; free activities are checked against user_id
        model_docid_actids = defaultdict(lambda: defaultdict(list))
        forbidden_ids = []
        for activity in activities.sudo():
            if activity.res_model:
                model_docid_actids[activity.res_model][activity.res_id].append(activity.id)
            elif activity.user_id.id != self.env.uid:
                forbidden_ids.append(activity.id)

        for doc_model, docid_actids in model_docid_actids.items():
            allowed = self.env['mail.message']._filter_records_for_message_operation(doc_model, docid_actids, operation)
            for document_id in [doc_id for doc_id in docid_actids if doc_id not in allowed.ids]:
                forbidden_ids.extend(docid_actids[document_id])

        if forbidden_ids:
            forbidden = self.browse(forbidden_ids)
            if result:
                result = (result[0] + forbidden, result[1])
            else:
                result = (forbidden, lambda: forbidden._make_access_error(operation))

        return result