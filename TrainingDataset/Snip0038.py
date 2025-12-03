class Budget(object):

    def __init__(self, template_categories_to_budget_map):
        self.categories_to_budget_map = template_categories_to_budget_map

    def override_category_budget(self, category, amount):
        self.categories_to_budget_map[category] = amount
