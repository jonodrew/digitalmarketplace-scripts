#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sets supplier "on framework" status for all supplier IDs read from file. Each file line should contain one supplier ID.

Usage:
    scripts/update-framework-results.py <framework> <stage> (--pass | --fail) --api-token=<token> <ids_file>

Example:
    python scripts/update-framework-results.py g-cloud-8 preview --pass --api-token=myToken ./g8-suppliers.txt

"""

import sys
sys.path.insert(0, '.')

import getpass

from docopt import docopt

from dmapiclient import DataAPIClient

from dmscripts.helpers.env import get_api_endpoint_from_stage
from dmscripts.logging import configure_logger
from dmscripts.framework_utils import set_framework_result


logger = configure_logger()

if __name__ == '__main__':
    arguments = docopt(__doc__)

    framework_slug = arguments['<framework>']
    data_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'api')
    client = DataAPIClient(data_api_url, arguments['--api-token'])
    user = getpass.getuser()
    result = True if arguments['--pass'] else False

    with open(arguments['<ids_file>'], 'r') as f:
        supplier_ids = filter(None, [l.strip() for l in f.readlines()])

    for supplier_id in supplier_ids:
        logger.info(set_framework_result(client, framework_slug, supplier_id, result, user))
    logger.info("DONE")
