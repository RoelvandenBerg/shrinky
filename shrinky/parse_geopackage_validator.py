import json
from pathlib import Path

FILTER_LIST = ['RQ5', 'RQ15']


def parse_geopackage_validator_results(path):
    explicit_records = parse_geopackage_validator_result(path)
    explicit_record_string = ''
    for table_name, id_list in explicit_records.items():
        id_list = ','.join(map(str, id_list))
        explicit_record_string += f"{table_name}:{id_list};"

    explicit_record_string = explicit_record_string[:-1]

    print(explicit_record_string)


def parse_geopackage_validator_result(path):
    in_file = Path(path)

    with open(in_file, "r") as content:
        validation_result = json.load(content)

    locations = []
    for result in validation_result['results']:
        if result['validation_code'] in FILTER_LIST:
            locations += result['locations']

    explicit_records = {}
    for location in locations:
        table_name = None
        row_id = None

        if 'table: ' in location:
            table_name = location.split('table: ')[1].split(', column')[0]

        if 'Error layer: ' in location:
            table_name = location.split('Error layer: ')[1].split(', found')[0]

        if ', example id ' in location:
            row_id = location.split(', example id ')[1]

        if ', example id: ' in location:
            row_id = location.split(', example id: ')[1]

        if table_name is None or row_id is None:
            continue

        if table_name not in explicit_records:
            explicit_records[table_name] = set()

        explicit_records[table_name].add(row_id)

    return explicit_records
