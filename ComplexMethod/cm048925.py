def _process_documents_web_services(self, job_count=None, with_commit=True):
        ''' Post and cancel all the documents that need a web service.

        :param job_count:   The maximum number of jobs to process if specified.
        :param with_commit: Flag indicating a commit should be made between each job.
        :return:            The number of remaining jobs to process.
        '''
        all_jobs = self.filtered(lambda d: d.edi_format_id._needs_web_services())._prepare_jobs()
        jobs_to_process = all_jobs[0:job_count] if job_count else all_jobs

        for job in jobs_to_process:
            documents = job['documents']
            move_to_lock = documents.move_id
            attachments_potential_unlink = documents.sudo().attachment_id.filtered(lambda a: not a.res_model and not a.res_id)
            try:
                documents.lock_for_update()
                move_to_lock.lock_for_update()
                attachments_potential_unlink.lock_for_update()
            except LockError:
                _logger.debug('Another transaction already locked documents rows. Cannot process documents.')
                if not with_commit:
                    raise UserError(_('This document is being sent by another process already. ')) from None
                continue
            self._process_job(job)
            if with_commit and len(jobs_to_process) > 1:
                self.env.cr.commit()

        return len(all_jobs) - len(jobs_to_process)