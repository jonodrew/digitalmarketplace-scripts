#!/usr/bin/env python

"""
Description:
    upload_dos_opportunities_email_list

Usage:
    upload_dos_opportunities_email_list.py <stage> <api_token> <mailchimp_username> <mailchimp_api_key>

Example:
    upload_dos_opportunities_email_list.py preview myToken user@gds.gov.uk 7483crh87h34c3

"""

import sys

from docopt import docopt
from dmapiclient import DataAPIClient
from dmutils.email.dm_mailchimp import DMMailChimpClient

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.upload_dos_opportunities_email_list import main
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging


logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


if __name__ == '__main__':
    arguments = docopt(__doc__)

    lots = [
        {
            "lot_slug": "digital-specialists",
            "list_id": "prod_list_id" if arguments['<stage>'] == "production" else "07c21f0451",
            "framework_slug": "digital-outcomes-and-specialists-2"
        },
        {
            "lot_slug": "digital-outcomes",
            "list_id": "prod_list_id2" if arguments['<stage>'] == "production" else "f0077c516d",
            "framework_slug": "digital-outcomes-and-specialists-2"
        },
        {
            "lot_slug": "user-research-participants",
            "list_id": "prod_list_id3" if arguments['<stage>'] == "production" else "d35601203b",
            "framework_slug": "digital-outcomes-and-specialists-2"
        }
    ]

    api_url = get_api_endpoint_from_stage(arguments['<stage>'])
    data_api_client = DataAPIClient(api_url, arguments['<api_token>'])
    dm_mailchimp_client = DMMailChimpClient(arguments['<mailchimp_username>'], arguments['<mailchimp_api_key>'], logger)

    for lot_data in lots:
        main(data_api_client, dm_mailchimp_client, lot_data, logger)
