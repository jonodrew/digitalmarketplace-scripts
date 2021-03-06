#!/usr/bin/env python
"""
Our data retention policy is that supplier declarations are removed 3 years after a framework's expiry date.

This script is very simple and has not been upgraded to accept any arguments to prevent the possibility of accidental
deletion. If you are in doubt use the dry run option.

Usage: data-retention-remove-supplier-declarations.py <stage> [--dry-run] [--verbose]

Options:
    --stage=<stage>                                       Stage to target

    --dry-run                                             List account that would have data stripped
    --verbose
    -h, --help                                            Show this screen

Examples:
    ./scripts/data-retention-remove-supplier-declarations.py preview
    ./scripts/data-retention-remove-supplier-declarations.py preview --dry-run --verbose

"""
import logging
import sys
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

logger = logging.getLogger("script")

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.data_retention_remove_supplier_declarations import remove_supplier_data


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    stage = arguments['<stage>']

    dry_run = arguments['--dry-run']
    verbose = arguments['--verbose']

    # Set defaults, instantiate clients
    logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )
    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )
    remove_supplier_data(data_api_client=data_api_client, logger=logger, dry_run=dry_run)
