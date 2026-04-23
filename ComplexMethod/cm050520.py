def test_burndown_chart(self):
        burndown_chart_domain = [('project_id', '!=', False)]
        project_domain = [('project_id', '=', self.project.id)]

        # Check that we get the expected results for the complete data of `self.project`.
        project_expected_dict = {
            ('January %s' % (self.current_year - 1), self.todo_stage.id): 5,
            ('February %s' % (self.current_year - 1), self.todo_stage.id): 2,
            ('February %s' % (self.current_year - 1), self.in_progress_stage.id): 3,
            ('March %s' % (self.current_year - 1), self.in_progress_stage.id): 5,
            ('April %s' % (self.current_year - 1), self.in_progress_stage.id): 3,
            ('April %s' % (self.current_year - 1), self.testing_stage.id): 2,
            ('May %s' % (self.current_year - 1), self.in_progress_stage.id): 2,
            ('May %s' % (self.current_year - 1), self.testing_stage.id): 3,
            ('June %s' % (self.current_year - 1), self.in_progress_stage.id): 1,
            ('June %s' % (self.current_year - 1), self.testing_stage.id): 4,
            ('July %s' % (self.current_year - 1), self.testing_stage.id): 5,
            ('August %s' % (self.current_year - 1), self.testing_stage.id): 4,
            ('August %s' % (self.current_year - 1), self.done_stage.id): 1,
            ('September %s' % (self.current_year - 1), self.testing_stage.id): 3,
            ('September %s' % (self.current_year - 1), self.done_stage.id): 2,
            ('October %s' % (self.current_year - 1), self.testing_stage.id): 2,
            ('October %s' % (self.current_year - 1), self.done_stage.id): 3,
            ('November %s' % (self.current_year - 1), self.testing_stage.id): 1,
            ('November %s' % (self.current_year - 1), self.done_stage.id): 4,
            ('December %s' % (self.current_year - 1), self.todo_stage.id): 1,
            ('December %s' % (self.current_year - 1), self.done_stage.id): 5,
        }
        project_expected_is_closed_dict = {
            ('January %s' % (self.current_year - 1), 'open'): 5,
            ('February %s' % (self.current_year - 1), 'open'): 5,
            ('March %s' % (self.current_year - 1), 'open'): 5,
            ('April %s' % (self.current_year - 1), 'open'): 5,
            ('May %s' % (self.current_year - 1), 'open'): 5,
            ('June %s' % (self.current_year - 1), 'open'): 5,
            ('July %s' % (self.current_year - 1), 'open'): 5,
            ('August %s' % (self.current_year - 1), 'open'): 4,
            ('August %s' % (self.current_year - 1), 'closed'): 1,
            ('September %s' % (self.current_year - 1), 'open'): 3,
            ('September %s' % (self.current_year - 1), 'closed'): 2,
            ('October %s' % (self.current_year - 1), 'open'): 2,
            ('October %s' % (self.current_year - 1), 'closed'): 3,
            ('November %s' % (self.current_year - 1), 'open'): 1,
            ('November %s' % (self.current_year - 1), 'closed'): 4,
            ('December %s' % (self.current_year - 1), 'closed'): 6,
        }
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
        current_month = datetime.now().month
        for i in range(current_month):
            month_key = f"{months[i]} {self.current_year}"
            project_expected_dict[(month_key, self.todo_stage.id)] = 1
            project_expected_dict[(month_key, self.done_stage.id)] = 5
            project_expected_is_closed_dict[(month_key, 'closed')] = 6

        # Check that we get the expected results for the complete data of `self.project`.
        self.check_read_group_results(Domain.AND([burndown_chart_domain, project_domain]), project_expected_dict)
        self.check_read_group_is_closed_results(Domain.AND([burndown_chart_domain, project_domain]), project_expected_is_closed_dict)

        # Check that we get the expected results for the complete data of `self.project` & `self.project_2` using an
        # `ilike` in the domain.
        all_projects_domain_with_ilike = Domain.OR([project_domain, [('project_id', 'ilike', 'mySearchTag')]])
        project_expected_dict = {key: val if key[1] != self.todo_stage.id else val + 2 for key, val in project_expected_dict.items()}
        project_expected_is_closed_dict = {key: val if key[1] == 'closed' else val + 2 for key, val in project_expected_is_closed_dict.items()}
        for i in range(2, 11):
            month_key = f"{months[i]} {self.current_year - 1}"
            project_expected_dict[(month_key, self.todo_stage.id)] = 2
        project_expected_is_closed_dict[(f"{months[11]} {self.current_year - 1}", 'open')] = 2
        for i in range(current_month):
            project_expected_is_closed_dict[(f"{months[i]} {self.current_year}", 'open')] = 2
        self.check_read_group_results(Domain.AND([burndown_chart_domain, all_projects_domain_with_ilike]), project_expected_dict)
        self.check_read_group_is_closed_results(Domain.AND([burndown_chart_domain, all_projects_domain_with_ilike]), project_expected_is_closed_dict)

        date_from, date_to = ('%s-01-01' % (self.current_year - 1), '%s-03-01' % (self.current_year - 1))
        date_from_is_closed, date_to_is_closed = ('%s-10-01' % (self.current_year - 1), '%s-12-01' % (self.current_year - 1))

        date_and_user_domain = [('date', '>=', date_from), ('date', '<', date_to), ('user_ids', 'ilike', 'ProjectUser')]
        complex_domain_expected_dict = {
            ('January %s' % (self.current_year - 1), self.todo_stage.id): 3,
            ('February %s' % (self.current_year - 1), self.todo_stage.id): 1,
            ('February %s' % (self.current_year - 1), self.in_progress_stage.id): 2,
        }
        complex_domain = Domain.AND([burndown_chart_domain, all_projects_domain_with_ilike, date_and_user_domain])
        self.check_read_group_results(complex_domain, complex_domain_expected_dict)

        date_and_user_domain = [('date', '>=', date_from_is_closed), ('date', '<', date_to_is_closed), ('user_ids', 'ilike', 'ProjectUser')]
        complex_domain = Domain.AND([burndown_chart_domain, all_projects_domain_with_ilike, date_and_user_domain])
        complex_domain_expected_dict = {
            ('October %s' % (self.current_year - 1), 'closed'): 2.0,
            ('October %s' % (self.current_year - 1), 'open'): 1.0,
            ('November %s' % (self.current_year - 1), 'closed'): 2.0,
            ('November %s' % (self.current_year - 1), 'open'): 1.0
        }
        self.check_read_group_is_closed_results(complex_domain, complex_domain_expected_dict)

        date_and_user_domain = [('date', '>=', date_from), ('date', '<', date_to), ('user_ids', 'ilike', 'ProjectManager')]
        milestone_domain = [('milestone_id', 'ilike', 'Test')]
        complex_domain = Domain.AND([burndown_chart_domain, all_projects_domain_with_ilike, date_and_user_domain, milestone_domain])
        complex_domain_expected_dict = {
            ('January %s' % (self.current_year - 1), self.todo_stage.id): 1,
            ('February %s' % (self.current_year - 1), self.todo_stage.id): 1,
        }
        self.check_read_group_results(complex_domain, complex_domain_expected_dict)

        date_and_user_domain = [('date', '>=', date_from_is_closed), ('date', '<', date_to_is_closed), ('user_ids', 'ilike', 'ProjectManager')]
        milestone_domain = [('milestone_id', 'ilike', 'Test')]
        complex_domain = Domain.AND([burndown_chart_domain, all_projects_domain_with_ilike, date_and_user_domain, milestone_domain])
        complex_domain_expected_dict = {
            ('October %s' % (self.current_year - 1), 'open'): 1.0,
            ('November %s' % (self.current_year - 1), 'closed'): 1.0
        }
        self.check_read_group_is_closed_results(complex_domain, complex_domain_expected_dict)