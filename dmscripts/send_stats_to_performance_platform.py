import base64
import requests

from datetime import datetime, timedelta

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

HOURLY_TIME_FORMAT = '%Y-%m-%dT%H:00:00+00:00'  # On the hour exactly
DAILY_TIME_FORMAT = '%Y-%m-%dT00:00:00+00:00'  # Midnight
PERFORMANCE_PLATFORM_URL_TEMPLATES = {
    "day": {
        "stage": "https://www.performance.service.gov.uk/data/{pp_service}/applications-by-stage",
        "lot": "https://www.performance.service.gov.uk/data/{pp_service}/applications-by-lot",
    },
    "hour": {
        "stage": "https://www.performance.service.gov.uk/data/{pp_service}/applications-by-stage-realtime",
        "lot": "https://www.performance.service.gov.uk/data/{pp_service}/applications-by-lot-realtime",
    },
}

logger = logging_helpers.configure_logger({'dmapiclient': logging.WARNING})


def _format_statistics(stats, category, groupings):
    """Filter statistics according to specified groupings

    :param stats: Framework statistics as returned by our API
    :param category: Top-level key from the statistics that we want to filter, e.g. 'interested_suppliers'
    :param groupings: Rules about how data should be grouped, with new keys specified along with a set of conditions
                      that must be met for data to be included under that key.
                      Lists will match with any values that are in the list, and exact values are matched exactly.
                      e.g.
                       'interested': {
                            'declaration_status': [None, 'started'],
                            'has_completed_services': False
                        }
                      Will result in a key 'interested' in the return value that has a count of 'interested_suppliers'
                      with a declaration status in [None or 'started'] and 'has_completed_services' == False
    :return: A dictionary of statistics formatted according to the specified groupings
    """
    return _label_and_count(stats[category], groupings)


def _label_and_count(stats, groupings):
    data = {
        label: _sum_counts(stats, filters)
        for label, filters in groupings.items()
    }
    return data


def _sum_counts(stats, filter_by=None, sum_by='count'):
    return sum(
        statistic[sum_by] for statistic in stats
        if not filter_by or all(
            _find(statistic.get(key), value)
            for key, value in filter_by.items()
        )
    )


def _find(statistic, filter_value):
    if isinstance(filter_value, list):
        return statistic in filter_value
    else:
        return statistic == filter_value


def _generate_id(timestamp, period, data_type, data_item, pp_service):
    # Instructions from Performance Platform:
    # _id should be a unique url-friendly, base64-encoded, UTF8 encoded concatenation identifier, formed from:
    # _timestamp, service (= e.g. gcloud), period (= day or hour), dataType (= applications-by-stage/lot), stage/lot
    id_bytes = "-".join((timestamp, pp_service, period, data_type, data_item,)).encode('utf-8')
    return base64.b64encode(id_bytes).decode('utf-8')


def send_data(data, url, pp_bearer):
    # Equivalent to
    # curl -X POST -d '<payload>' -H 'Content-type: application/json' -H 'Authorization: Bearer <bearer-token>' <url>
    logger.info(u"Sending data to Performance Platform dataset '{url}':\n{data}", extra={'url': url, 'data': data})
    res = requests.post(url, json=data, headers={'Authorization': 'Bearer {}'.format(pp_bearer)})
    if res.status_code != 200:
        logger.error(
            u"Failed to send data: {code}: {cause}",
            extra={'code': res.status_code, 'cause': res.json().get('message', res.text)}
        )
    return res.status_code


def applications_by_stage(stats):
    return _format_statistics(
        stats,
        'interested_suppliers',
        {
            'interested': {
                'declaration_status': [None, 'started'],
                'has_completed_services': False
            },
            'made-declaration': {
                'declaration_status': 'complete',
                'has_completed_services': False
            },
            'completed-services': {
                'declaration_status': [None, 'started'],
                'has_completed_services': True
            },
            'eligible': {
                'declaration_status': 'complete',
                'has_completed_services': True
            }
        }
    )


def services_by_lot(stats, framework):
    return _format_statistics(
        stats,
        'services',
        {
            lot['slug']: {
                'lot': lot['slug'],
                'status': 'submitted',
            } for lot in framework['lots']
        }
    )


def send_by_stage_stats(stats, timestamp_string, period, pp_bearer, pp_service):
    data_type = "applications-by-stage"
    processed_stats = applications_by_stage(stats)
    data = [{
        "_id": _generate_id(timestamp_string, period, data_type, stage, pp_service),
        "_timestamp": timestamp_string,
        "service": pp_service,
        "stage": stage,
        "count": processed_stats.get(stage, 0),
        "dataType": data_type,
        "period": period
    } for stage in processed_stats]

    return send_data(data, PERFORMANCE_PLATFORM_URL_TEMPLATES[period]['stage'].format(pp_service=pp_service), pp_bearer)


def send_by_lot_stats(stats, timestamp_string, period, framework, pp_bearer, pp_service):
    data_type = "applications-by-lot"
    processed_stats = services_by_lot(stats, framework)
    data = [{
        "_id": _generate_id(timestamp_string, period, data_type, lot, pp_service),
        "_timestamp": timestamp_string,
        "service": pp_service,
        "lot": lot,
        "count": processed_stats.get(lot, 0),
        "dataType": data_type,
        "period": period
    } for lot in processed_stats]

    return send_data(data, PERFORMANCE_PLATFORM_URL_TEMPLATES[period]['lot'].format(pp_service=pp_service), pp_bearer)


def send_framework_stats(data_api_client, framework_slug, period, pp_bearer, pp_service):
    stats = data_api_client.get_framework_stats(framework_slug)
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    now = datetime.utcnow()
    # _timestamp is the *start* of the period to which the data relates but the "reading" here is at the *end*
    # of the period, so need to subtract the period from the current time
    timestamp_string = (
        (now - timedelta(days=1)).strftime(DAILY_TIME_FORMAT)
        if period == 'day' else
        (now - timedelta(hours=1)).strftime(HOURLY_TIME_FORMAT)
    )
    res1 = send_by_stage_stats(stats, timestamp_string, period, pp_bearer, pp_service)
    res2 = send_by_lot_stats(stats, timestamp_string, period, framework, pp_bearer, pp_service)
    return res1 == res2 == 200
