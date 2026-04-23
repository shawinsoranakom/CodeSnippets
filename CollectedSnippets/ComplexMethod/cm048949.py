def _compute_matching_skill_ids(self):
        matching_job_id = self.env.context.get("matching_job_id")
        matching_job = self.env["hr.job"].browse(matching_job_id)
        for applicant in self:
            job = matching_job or applicant.job_id
            if not job or not (job.job_skill_ids or job.expected_degree):
                applicant.matching_skill_ids = False
                applicant.missing_skill_ids = False
                applicant.matching_score = False
                continue
            job_skills = job.job_skill_ids
            job_degree = job.expected_degree.sudo().score * 100
            job_total = sum(job_skills.mapped("level_progress")) + job_degree
            job_skill_map = {js.skill_id: js.level_progress for js in job_skills}

            matching_applicant_skills = applicant.current_applicant_skill_ids.filtered(
                lambda a: a.skill_id in job_skill_map,
            )
            applicant_degree = applicant.type_id.score * 100 if job_degree > 1 else 0
            applicant_total = (
                sum(min(skill.level_progress, job_skill_map[skill.skill_id] * 2) for skill in matching_applicant_skills)
                + applicant_degree
            )

            matching_skill_ids = matching_applicant_skills.mapped("skill_id")
            missing_skill_ids = job_skills.mapped("skill_id") - matching_applicant_skills.mapped("skill_id")
            matching_score = round(applicant_total / job_total * 100) if job_total else 0

            applicant.matching_skill_ids = matching_skill_ids
            applicant.missing_skill_ids = missing_skill_ids
            applicant.matching_score = matching_score