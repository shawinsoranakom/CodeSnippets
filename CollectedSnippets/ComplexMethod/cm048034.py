def _compute_dates(self):
        for lot in self:
            if not lot.product_id.use_expiration_date:
                lot.use_date = False
                lot.removal_date = False
                lot.alert_date = False
            elif lot.expiration_date:
                # when create
                if lot.product_id != lot._origin.product_id or \
                   (not lot.use_date and not lot.removal_date and not lot.alert_date) or \
                   (lot.expiration_date and not lot._origin.expiration_date):
                    product_tmpl = lot.product_id.product_tmpl_id
                    lot.use_date = lot.expiration_date - datetime.timedelta(days=product_tmpl.use_time)
                    lot.removal_date = lot.expiration_date - datetime.timedelta(days=product_tmpl.removal_time)
                    lot.alert_date = lot.expiration_date - datetime.timedelta(days=product_tmpl.alert_time)
                # when change
                elif lot._origin.expiration_date:
                    time_delta = lot.expiration_date - lot._origin.expiration_date
                    lot.use_date = lot._origin.use_date and lot._origin.use_date + time_delta
                    lot.removal_date = lot._origin.removal_date and lot._origin.removal_date + time_delta
                    lot.alert_date = lot._origin.alert_date and lot._origin.alert_date + time_delta