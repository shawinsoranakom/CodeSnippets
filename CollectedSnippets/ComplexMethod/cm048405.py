def _get_gather_domain(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
        domains = [Domain('product_id', '=', product_id.id)]
        if not strict:
            if lot_id:
                domains.append(Domain('lot_id', 'in', [lot_id.id, False]))
            if package_id:
                domains.append(Domain('package_id', '=', package_id.id))
            if owner_id:
                domains.append(Domain('owner_id', '=', owner_id.id))
            domains.append(Domain('location_id', 'child_of', location_id.id))
        else:
            domains.extend((
                Domain('lot_id', 'in', [False, lot_id.id if lot_id else False]),
                Domain('package_id', '=', package_id.id if package_id else False),
                Domain('owner_id', '=', owner_id.id if owner_id else False),
                Domain('location_id', '=', location_id.id),
            ))
        if self.env.context.get('with_expiration'):
            domains.append(Domain('removal_date', '>=', self.env.context['with_expiration']) | Domain('removal_date', '=', False))
        return Domain.AND(domains)