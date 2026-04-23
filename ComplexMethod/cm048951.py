def _compute_applicant_matching_score(self):
        active_applicant_id = self.env.context.get("active_applicant_id")
        if not active_applicant_id:
            for job in self:
                job.applicant_matching_score = False
            return

        applicant = self.env["hr.applicant"].browse(active_applicant_id)
        for job in self:
            if not job.job_skill_ids:
                job.applicant_matching_score = False
                continue
            job_skills = job.job_skill_ids
            job_degree = job.expected_degree.score * 100
            job_total = sum(job.job_skill_ids.mapped("level_progress")) + job_degree
            job_skill_map = {js.skill_id.id: js.level_progress for js in job_skills}

            matching_applicant_skills = applicant.current_applicant_skill_ids.filtered(
                lambda a: a.skill_id.id in job_skill_map,
            )
            applicant_degree = applicant.type_id.score * 100 if job_degree > 1 else 0
            applicant_total = (
                sum(
                    min(skill.level_progress, job_skill_map[skill.skill_id.id] * 2)
                    for skill in matching_applicant_skills
                )
                + applicant_degree
            )

            job.applicant_matching_score = applicant_total / job_total * 100