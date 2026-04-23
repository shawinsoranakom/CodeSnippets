async def _async_update_data(self) -> FireflyCoordinatorData:
        """Fetch data from Firefly III API."""
        now = datetime.now()
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now

        try:
            (
                accounts,
                categories,
                primary_currency,
                budgets,
                bills,
            ) = await asyncio.gather(
                self.firefly.get_accounts(),
                self.firefly.get_categories(),
                self.firefly.get_currency_primary(),
                self.firefly.get_budgets(start=start_date, end=end_date),
                self.firefly.get_bills(),
            )

            category_details = await asyncio.gather(
                *(
                    self.firefly.get_category(
                        category_id=int(category.id),
                        start=start_date,
                        end=end_date,
                    )
                    for category in categories
                )
            )
        except FireflyAuthenticationError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
                translation_placeholders={"error": repr(err)},
            ) from err
        except FireflyConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": repr(err)},
            ) from err
        except FireflyTimeoutError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="timeout_connect",
                translation_placeholders={"error": repr(err)},
            ) from err

        return FireflyCoordinatorData(
            accounts={account.id: account for account in accounts},
            categories=categories,
            category_details={category.id: category for category in category_details},
            budgets={budget.id: budget for budget in budgets},
            bills=bills,
            primary_currency=primary_currency,
        )