#!/usr/bin/env python
"""

For a DOS-type framework this will export details of all "digital-outcomes" services, including the types
of outcome the supplier provides and the locations they can provide them in.

Usage:
    scripts/export-dos-outcomes.py <stage> <framework_slug> <content_path>
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt

from dmapiclient import DataAPIClient
from dmcontent.content_loader import ContentLoader

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.csv_helpers import make_fields_from_content_questions, write_csv_with_make_row
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services
from dmutils.env_helpers import get_api_endpoint_from_stage


def find_all_outcomes(client):
    return find_suppliers_with_details_and_draft_services(client,
                                                          FRAMEWORK_SLUG,
                                                          lot="digital-outcomes",
                                                          statuses="submitted"
                                                          )


def make_row(capabilities, locations):
    def inner(record):
        row = [
            ("supplier_id", record["supplier_id"]),
            ("supplier_name", record['supplier']['name']),
            ("supplier_declaration_name", record['declaration'].get('supplierRegisteredName', '')),
            ("status", "PASSED" if record["onFramework"] else "FAILED"),
        ]
        return row + make_fields_from_content_questions(capabilities + locations, record)

    return inner


def get_team_capabilities(content_manifest):
    section = content_manifest.get_section("team-capabilities")

    return [
        question.questions[0]
        for question in section.questions
    ]


def get_outcomes_locations(content_manifest):
    return [
        content_manifest.get_question("locations")
    ]


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    CONTENT_PATH = arguments['<content_path>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    content_loader = ContentLoader(CONTENT_PATH)
    content_loader.load_manifest(FRAMEWORK_SLUG, "services", "edit_submission")
    content_manifest = content_loader.get_manifest(FRAMEWORK_SLUG, "edit_submission")

    capabilities = get_team_capabilities(content_manifest)
    locations = get_outcomes_locations(content_manifest)
    suppliers = find_all_outcomes(client)

    write_csv_with_make_row(
        suppliers,
        make_row(capabilities, locations),
        "output/{}-outcomes.csv".format(FRAMEWORK_SLUG)
    )
