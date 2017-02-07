#!/usr/bin/env python
"""
This can be used to set a new alias to an existing Elasticsearch index, via the Search API

Usage:
    set-search-alias.py <stage> <search_api_token> <alias> <index>
"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmapiclient import SearchAPIClient


if __name__ == '__main__':
    arguments = docopt(__doc__)

    search_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'search-api')
    search_api_token = arguments['<search_api_token>']

    client = SearchAPIClient(search_api_url, arguments['<search_api_url>'])
    client.set_alias(arguments['<alias>'], arguments['<index>'])
