#!/usr/bin/env python

"""
Description:
    For every lot the script will:
        - look for latest briefs for Digital Outcomes and Specialists
        - if there are new briefs on that lot:
            - it will create a Mailchimp campaign
            - it will set the content of the campaign to be the briefs found
            - it will send that campaign to the list_id as referenced in the `lots` variable
        - if there are no new briefs on that lot no campaign is created or sent

    Number of days tells the script for how many days before current date it should include in its search for briefs
        example:  if you run this script on a Wednesday and set number of days=1,
                    then it will only include briefs from Tuesday (preceding day).
        example2: if you run it on Wednesday and set number of days=3,
                    then it will include all briefs published on Sunday, Monday and Tuesday.
    By default, the script will send 3 days of briefs on a Monday (briefs from Fri, Sat, Sun) and 1 day on all other
    days. This can be overrriden as described above.

    For testing purposes, you can override the list ID so you can send it to yourself only as
    we have set up a testing list with ID "096e52cebb"

    If you only need to send opportunities for one lot rather than all of them, you can also do this via the command
    line. Note, this may come in useful if the script was to fail halfway and you wish to continue from the lot which
    failed.

Usage:
    send-dos-opportunities-email.py <stage> <mailchimp_username> <mailchimp_api_key> <framework_slug>
        [--number_of_days=<number_of_days>] [--list_id=<list_id>] [--lot_slug=<lot_slug>]

Example:
    send-dos-opportunities-email.py
        preview user@gds.gov.uk 7483crh87h34c3 digital-outcomes-and-specialists-3
        --number_of_days=3 --list_id=988972hse --lot_slug=digital-outcomes
"""

import sys

from datetime import date

from docopt import docopt
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.send_dos_opportunities_email import main
from dmscripts.helpers import logging_helpers
from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = logging_helpers.configure_logger()


list_ids = {
    'digital-outcomes-and-specialists-2': {
        'digital-specialists': "30ba9fdf39",
        'digital-outcomes': "97952fee38",
        'user-research-participants': "e6b93a3bce",
    },
    'digital-outcomes-and-specialists-3': {
        'digital-specialists': "bee802d641",
        'digital-outcomes': "5c92c78a78",
        'user-research-participants': "34ebe0bffa",
    }
}

if __name__ == "__main__":
    arguments = docopt(__doc__)
    framework_slug = arguments['<framework_slug>']
    lots = [
        {
            "lot_slug": "digital-specialists",
            "lot_name": "Digital specialists",
            "list_id": list_ids[framework_slug]['digital-specialists']
        },
        {
            "lot_slug": "digital-outcomes",
            "lot_name": "Digital outcomes",
            "list_id": list_ids[framework_slug]['digital-outcomes']
        },
        {
            "lot_slug": "user-research-participants",
            "lot_name": "User research participants",
            "list_id": list_ids[framework_slug]['user-research-participants']
        }
    ]

    # Override number of days
    if arguments.get("--number_of_days"):
        number_of_days = int(arguments['--number_of_days'])
    else:
        day_of_week = date.today().weekday()
        if day_of_week == 0:
            number_of_days = 3  # If Monday, then 3 days of briefs
        else:
            number_of_days = 1

    # Override list for non-production environment
    if arguments['<stage>'] != "production":
        logger.info(
            "The environment is not production. Emails will be sent to test list unless you set the list id manually."
        )
        for lot in lots:
            lot.update({"list_id": "096e52cebb"})

    # Override list id
    if arguments.get("--list_id"):
        for lot in lots:
            lot.update({"list_id": arguments["--list_id"]})

    # Override lot
    if arguments.get("--lot_slug"):
        lots = [lot for lot in lots if lot["lot_slug"] == arguments["--lot_slug"]]

    api_url = get_api_endpoint_from_stage(arguments['<stage>'])
    data_api_client = DataAPIClient(api_url, get_auth_token('api', arguments['<stage>']))

    dm_mailchimp_client = DMMailChimpClient(arguments['<mailchimp_username>'], arguments['<mailchimp_api_key>'], logger)

    for lot_data in lots:
        ok = main(
            data_api_client=data_api_client,
            mailchimp_client=dm_mailchimp_client,
            lot_data=lot_data,
            number_of_days=number_of_days,
            framework_slug=framework_slug,
        )
        if not ok:
            sys.exit(1)
