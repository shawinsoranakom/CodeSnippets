def upgrade(file_manager):
    log = logging.getLogger(__name__)

    MODS_WITH_DYNAMIC_DOMESTIC_FP = {'l10n_in'}
    DEFINED_DOMESTIC_FP = {
        'l10n_ch': 'fiscal_position_template_1',
        'l10n_fr_account': 'fiscal_position_template_domestic',
    }

    SRC_FIELD = 'tax_ids/tax_src_id'
    DEST_FIELD = 'tax_ids/tax_dest_id'
    fiscal_position_data_files = [
        file for file in file_manager
        if file.path.suffix in ('.csv')
        and 'account.fiscal.position' in file.path.name
    ]
    fiscal_position_file_names = {f.path.parts[-1] for f in fiscal_position_data_files}
    nb_fiscal_position_files = len(fiscal_position_data_files)

    tax_data_files = [
        file for file in file_manager
        if file.path.suffix in ('.csv')
        and 'account.tax-' in file.path.name
    ]
    nb_tax_files = len(tax_data_files)

    eu_b2c_fps = {}
    tax_positions = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(fp=set(), replaces=set()))))  # {module_name: {coa_name: { tax_x: {fp: {fiscal_position_1,fiscal_position_2}, replaces: {tax1}}}}
    for i, file in enumerate(fiscal_position_data_files, start=1):
        file_manager.print_progress(i, nb_fiscal_position_files, file.path)

        module_name = file.path.parts[-4]
        csv_file = csv.DictReader(file.content.splitlines())
        csv_data = list(csv_file)
        field_names = csv_file.fieldnames
        if SRC_FIELD not in field_names or DEST_FIELD not in field_names:
            log.warning("No src and dest fields in %s...skipping", file.path.parts[-1])
            continue

        has_country = 'country_id' in field_names

        buffer = StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                f
                for f in field_names + ([] if has_country else ['country_id'])
                if f not in (SRC_FIELD, DEST_FIELD)
            ],
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            lineterminator='\n',
        )
        writer.writeheader()

        domestic_fp_id = f'{module_name}_domestic_fiscal_position'
        module_country = module_name[5:7] if module_name.startswith('l10n_') else 'us'
        domestic_fp_name = f'{module_country.upper()} Domestic'
        coa_name = file.path.parts[-1].split("position-")[1].replace(".csv", "")
        fiscal_position = ''
        for row_nb, row in enumerate(csv_data, start=1):
            fiscal_position = row['id'] or fiscal_position
            if row.get('country_group_id') == 'account.europe_vat' and row.get('auto_apply') and not row.get('country_id') and not row.get('vat_required'):
                eu_b2c_fps[module_country] = fiscal_position

            src_tax = row.pop(SRC_FIELD)
            dest_tax = row.pop(DEST_FIELD)
            if row_nb == 1:
                # copy the first fiscal position to create a generic domestic fiscal position
                # if the first fiscal position doesn't have a country matching the module
                # otherwise assume the first one is the domestic fp
                dom_fp_data = {
                    **row,
                    'id': domestic_fp_id,
                    'name': domestic_fp_name,
                }
                if (
                    module_name not in MODS_WITH_DYNAMIC_DOMESTIC_FP
                    and module_name not in DEFINED_DOMESTIC_FP
                    and (not has_country or row.get('country_id') != f'base.{module_country}')
                ):
                    dom_fp_data['country_id'] = f'base.{module_country}'
                    writer.writerow(dom_fp_data)
                else:
                    domestic_fp_id = DEFINED_DOMESTIC_FP.get(module_name) or row['id']

            if src_tax and dest_tax:
                existing_src_tax_fp = tax_positions[module_name][coa_name][src_tax]['fp']
                if existing_src_tax_fp and domestic_fp_id not in existing_src_tax_fp:
                    log.info("In module: %s, Src Tax: %s will be assigned to multiple Fiscal Positions: %s.", module_name, src_tax, f"{','.join(existing_src_tax_fp)},{domestic_fp_id}")
                if module_name not in MODS_WITH_DYNAMIC_DOMESTIC_FP:
                    tax_positions[module_name][coa_name][src_tax]['fp'].add(domestic_fp_id)
                    if eub2c_position := eu_b2c_fps.get(module_country):
                        tax_positions[module_name][coa_name][src_tax]['fp'].add(eub2c_position)

                existing_dest_tax_fp = tax_positions[module_name][coa_name][dest_tax]['fp']
                if existing_dest_tax_fp and fiscal_position not in existing_dest_tax_fp:
                    log.info("In module: %s, Dest Tax: %s will be assigned to multiple Fiscal Positions: %s.", module_name, dest_tax, f"{','.join(existing_dest_tax_fp)},{fiscal_position}")
                tax_positions[module_name][coa_name][dest_tax]['fp'].add(fiscal_position)

                tax_positions[module_name][coa_name][dest_tax]['replaces'].add(src_tax)
                if row['id']:
                    writer.writerow(row)
            else:
                if src_tax:
                    log.warning("%s tax in module %s is mapped to nothing", src_tax, module_name)
                writer.writerow(row)

        file.content = buffer.getvalue()

    for i, file in enumerate(tax_data_files, start=1):
        file_manager.print_progress(i, nb_tax_files, file.path)

        module_name = file.path.parts[-4]
        coa_name = file.path.parts[-1].split("tax-")[1].replace(".csv", "")
        csv_file = csv.DictReader(file.content.splitlines())
        csv_data = list(csv_file)
        if (fpfile := f'account.fiscal.position-{coa_name}.csv') and fpfile not in fiscal_position_file_names:
            log.warning("Missing fiscal position file %s while processing %s", fpfile, module_name)
        is_primary_tax = 'name' in csv_file.fieldnames
        buffer = StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[fn for fn in csv_file.fieldnames if fn] + (['fiscal_position_ids', 'original_tax_ids'] if is_primary_tax else []),
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_ALL,
            lineterminator='\n',
            extrasaction='ignore',
        )
        writer.writeheader()
        for tax_row in csv_data:
            tax_id = tax_row['id']
            if tax_id and is_primary_tax:
                tax_info = tax_positions[module_name][coa_name][tax_id] if tax_id else {}
                new_fp = ','.join(tax_info.get('fp', []))
                new_alts = ','.join(tax_info.get('replaces', []))
                if not new_fp:
                    new_fp = FP_LOOKUP.get((coa_name, tax_id), "")
                writer.writerow({
                    **tax_row,
                    'fiscal_position_ids': new_fp,
                    'original_tax_ids': new_alts,
                })
            else:
                writer.writerow(tax_row)
        file.content = buffer.getvalue()