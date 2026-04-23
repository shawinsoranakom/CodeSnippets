def _gc_portal_users(self, batch_size=50):
        """Remove the portal users that asked to deactivate their account.

        (see <res.users>::_deactivate_portal_user)

        Removing a user can be an heavy operation on large database (because of
        create_uid, write_uid on each models, which are not always indexed). Because of
        that, this operation is done in a CRON.
        """
        delete_requests = self.search([("state", "=", "todo")])

        # filter the requests related to a deleted user
        done_requests = delete_requests.filtered(lambda request: not request.user_id)
        done_requests.state = "done"

        todo_requests = delete_requests - done_requests
        commit_progress = self.env['ir.cron']._commit_progress
        commit_progress(len(done_requests), remaining=len(todo_requests))

        for delete_request in todo_requests[:batch_size]:
            delete_request = delete_request.try_lock_for_update().filtered(lambda d: d.state == 'todo')
            if not delete_request:
                continue
            user = delete_request.user_id
            user_name = user.name
            partner = user.partner_id
            requester_name = delete_request.create_uid.name

            # Step 1: Delete User
            try:
                user.unlink()
                _logger.info(
                    "User #%i %r, deleted. Original request from %r.",
                    user.id, user_name, requester_name)
                delete_request.state = 'done'
                commit_progress(1)
            except Exception as e:
                self.env.cr.rollback()
                _logger.error(
                    "User #%i %r could not be deleted. Original request from %r. Related error: %s",
                    user.id, user_name, requester_name, e)
                delete_request.state = "fail"
                # commit and progress even when failed
                if commit_progress(1):
                    continue
                else:
                    break

            # Step 2: Delete Linked Partner
            #         Could be impossible if the partner is linked to a SO for example
            try:
                partner.unlink()
                _logger.info(
                    "Partner #%i %r, deleted. Original request from %r.",
                    partner.id, user_name, requester_name)
                if not commit_progress():
                    break
            except Exception as e:
                self.env.cr.rollback()
                _logger.warning(
                    "Partner #%i %r could not be deleted. Original request from %r. Related error: %s",
                    partner.id, user_name, requester_name, e)
                if not commit_progress():  # just check if we should stop
                    break