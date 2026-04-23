def upgrade() -> None:
    # Skip migration if STRIPE_API_KEY is not set
    if 'STRIPE_API_KEY' not in os.environ:
        print('Skipping migration 019: STRIPE_API_KEY not set')
        return

    stripe.api_key = os.environ['STRIPE_API_KEY']

    # Get all users from stripe
    user_id_to_customer_ids = defaultdict(list)
    customers = stripe.Customer.list()
    for customer in customers.auto_paging_iter():
        user_id = customer.metadata.get('user_id')
        if user_id:
            user_id_to_customer_ids[user_id].append(customer.id)

    # Canonical
    stripe_customers = {
        row[0]: row[1]
        for row in op.get_bind().execute(
            text('SELECT keycloak_user_id, stripe_customer_id FROM stripe_customers')
        )
    }

    to_delete = []
    for user_id, customer_ids in user_id_to_customer_ids.items():
        if len(customer_ids) == 1:
            continue
        canonical_customer_id = stripe_customers.get(user_id)
        if canonical_customer_id:
            for customer_id in customer_ids:
                if customer_id != canonical_customer_id:
                    to_delete.append({'user_id': user_id, 'customer_id': customer_id})
        else:
            # Prioritize deletion of items that don't have payment methods
            to_delete_for_customer = []
            for customer_id in customer_ids:
                payment_methods = stripe.Customer.list_payment_methods(customer_id)
                to_delete_for_customer.append(
                    {
                        'user_id': user_id,
                        'customer_id': customer_id,
                        'num_payment_methods': len(payment_methods),
                    }
                )
            to_delete_for_customer.sort(
                key=lambda c: c['num_payment_methods'], reverse=True
            )
            to_delete.extend(to_delete_for_customer[1:])

    for item in to_delete:
        op.get_bind().execute(
            text(
                'INSERT INTO script_results (revision, data) VALUES (:revision, :data)'
            ),
            {
                'revision': revision,
                'data': json.dumps(item),
            },
        )
        stripe.Customer.delete(item['customer_id'])