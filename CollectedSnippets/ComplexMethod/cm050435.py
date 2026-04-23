def _update_automated_probabilities(self):
        """ Recompute all the automated_probability (and align probability if both were aligned) for all the leads
        that are active (not won, nor lost).

        For performance matter, as there can be a huge amount of leads to recompute, this cron proceed by batch.
        Each batch is performed into its own transaction, in order to minimise the lock time on the lead table
        (and to avoid complete lock if there was only 1 transaction that would last for too long -> several minutes).
        If a concurrent update occurs, it will simply be put in the queue to get the lock.
        """
        pls_start_date = self._pls_get_safe_start_date()
        if not pls_start_date:
            return

        # 1. Get all the leads to recompute created after pls_start_date that are nor won nor lost
        pending_lead_domain = [
            ('stage_id', '!=', False),
            ('create_date', '>=', pls_start_date),
            ('won_status', '=', 'pending'),
        ]
        leads_to_update = self.env['crm.lead'].search(pending_lead_domain)
        leads_to_update_count = len(leads_to_update)

        # 2. Compute by batch to avoid memory error
        lead_probabilities = {}
        for i in range(0, leads_to_update_count, PLS_COMPUTE_BATCH_STEP):
            leads_to_update_part = leads_to_update[i:i + PLS_COMPUTE_BATCH_STEP]
            batch_probabilites, _unused = leads_to_update_part._pls_get_naive_bayes_probabilities(batch_mode=True)
            lead_probabilities.update(batch_probabilites)
        _logger.info("Predictive Lead Scoring : New automated probabilities computed")

        # 3. Group by new probability to reduce server roundtrips when executing the update
        probability_leads = defaultdict(list)
        for lead_id, probability in sorted(lead_probabilities.items()):
            probability_leads[probability].append(lead_id)

        # 4. Update automated_probability (+ probability if both were equal)
        update_sql = """UPDATE crm_lead
                        SET automated_probability = %s,
                            probability = CASE WHEN (probability = automated_probability OR probability is null)
                                               THEN (%s)
                                               ELSE (probability)
                                          END
                        WHERE id in %s"""

        # Update by a maximum number of leads at the same time, one batch by transaction :
        # - avoid memory errors
        # - avoid blocking the table for too long with a too big transaction
        transactions_count, transactions_failed_count = 0, 0
        cron_update_lead_start_date = datetime.now()
        auto_commit = not modules.module.current_test
        self.flush_model()
        for probability, probability_lead_ids in probability_leads.items():
            for lead_ids_current in tools.split_every(PLS_UPDATE_BATCH_STEP, probability_lead_ids):
                transactions_count += 1
                try:
                    self.env.cr.execute(update_sql, (probability, probability, tuple(lead_ids_current)))
                    # auto-commit except in testing mode
                    if auto_commit:
                        self.env.cr.commit()
                except Exception as e:
                    _logger.warning("Predictive Lead Scoring : update transaction failed. Error: %s" % e)
                    transactions_failed_count += 1
        self.invalidate_model()

        _logger.info(
            "Predictive Lead Scoring : All automated probabilities updated (%d leads / %d transactions (%d failed) / %d seconds)" % (
                leads_to_update_count,
                transactions_count,
                transactions_failed_count,
                (datetime.now() - cron_update_lead_start_date).total_seconds(),
            )
        )