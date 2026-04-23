def _get_score(self, **kwargs):
        score = super(AccountAnalyticApplicability, self)._get_score(**kwargs)
        if score == -1:
            return -1
        product = self.env['product.product'].browse(kwargs.get('product'))
        account = self.env['account.account'].browse(kwargs.get('account'))
        if self.account_prefix:
            account_prefixes = tuple(prefix for prefix in re.split("[,;]", self.account_prefix.replace(" ", "")) if prefix)
            if account.code and account.code.startswith(account_prefixes):
                score += 1
            else:
                return -1
        if self.product_categ_id:
            if product and product.categ_id == self.product_categ_id:
                score += 1
            else:
                return -1
        return score