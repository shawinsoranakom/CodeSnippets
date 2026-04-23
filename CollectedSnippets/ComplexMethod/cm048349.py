def _prepare_ewaybill_base_json_payload(self):

        def get_transaction_type(seller_details, dispatch_details, buyer_details, ship_to_details):
            """
                1 - Regular
                2 - Bill To - Ship To
                3 - Bill From - Dispatch From
                4 - Combination of 2 and 3
            """
            if seller_details != dispatch_details and buyer_details != ship_to_details:
                return 4
            elif seller_details != dispatch_details:
                return 3
            elif buyer_details != ship_to_details:
                return 2
            else:
                return 1

        def prepare_details(key_paired_function, partner_detail):
            return {
                f"{place}{key}": fun(partner)
                for key, fun in key_paired_function
                for place, partner in partner_detail
            }
        ewaybill_json = {
                # document details
                "supplyType": self.supply_type,
                "subSupplyType": self.type_id.sub_type_code,
                "docType": self.type_id.code,
                "transactionType": get_transaction_type(
                    self.partner_bill_from_id,
                    self.partner_ship_from_id,
                    self.partner_bill_to_id,
                    self.partner_ship_to_id
                ),
                "transDistance": str(self.distance),
                "docNo": self.document_number,
                "docDate": (self.document_date or fields.Datetime.now()).strftime("%d/%m/%Y"),
                # bill details
                **prepare_details(
                    key_paired_function={
                        'Gstin': lambda p: p.commercial_partner_id.vat or "URP",
                        'TrdName': lambda p: p.commercial_partner_id.name,
                        'StateCode': self._get_partner_state_code,
                    }.items(),
                    partner_detail={'from': self.partner_bill_from_id, 'to': self.partner_bill_to_id}.items()
                ),
                # shipping details
                **prepare_details(
                    key_paired_function={
                        "Addr1": lambda p: p.street and p.street[:120] or "",
                        "Addr2": lambda p: p.street2 and p.street2[:120] or "",
                        "Place": lambda p: p.city and p.city[:50] or "",
                        "Pincode": lambda p: int(p.zip) if p.country_id.code == "IN" else 999999,
                    }.items(),
                    partner_detail={'from': self.partner_ship_from_id, 'to': self.partner_ship_to_id}.items()
                ),
                "actToStateCode": self._get_partner_state_code(self.partner_ship_to_id),
                "actFromStateCode": self._get_partner_state_code(self.partner_ship_from_id),
        }
        return ewaybill_json