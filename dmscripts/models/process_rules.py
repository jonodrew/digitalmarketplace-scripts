from datetime import datetime
from dmutils.formats import DATE_FORMAT, DATETIME_FORMAT


def format_datetime_string_as_date(dt):
    return datetime.strptime(dt, DATETIME_FORMAT).strftime(DATE_FORMAT) if dt else None


def remove_username_from_email_address(ea):
    return '{}'.format(ea.split('@').pop()) if ea else None


def construct_brief_url(brief_id):
    return (
        'https://www.digitalmarketplace.service.gov.uk/'
        'digital-outcomes-and-specialists/opportunities/{}'.format(brief_id)
    )


def extract_id_from_user_info(user_data):
    return ','.join([str(user['id']) for user in user_data])
