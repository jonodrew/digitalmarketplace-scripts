import mock
from datetime import date

import pytest
from freezegun import freeze_time
from lxml import html

from dmscripts.send_dos_opportunities_email import (
    main,
    get_campaign_data,
    get_live_briefs_between_two_dates,
    get_html_content
)
from dmutils.email.dm_mailchimp import DMMailChimpClient


LOT_DATA = {
    "lot_slug": "digital-specialists",
    "lot_name": "Digital specialists",
    "list_id": "096e52cebb"
}


def test_get_live_briefs_between_two_dates():
    data_api_client = mock.Mock()
    brief_iter_values = [
        {"publishedAt": "2017-03-24T09:52:17.669156Z"},
        {"publishedAt": "2017-03-23T23:59:59.669156Z"},
        {"publishedAt": "2017-03-23T09:52:17.669156Z"},
        {"publishedAt": "2017-03-23T00:00:00.000000Z"},
        {"publishedAt": "2017-03-22T09:52:17.669156Z"},
        {"publishedAt": "2017-03-21T09:52:17.669156Z"},
        {"publishedAt": "2017-03-20T09:52:17.669156Z"},
        {"publishedAt": "2017-03-19T09:52:17.669156Z"},
        {"publishedAt": "2017-03-18T09:52:17.669156Z"},
        {"publishedAt": "2017-02-17T09:52:17.669156Z"}
    ]

    data_api_client.find_briefs_iter.return_value = iter(brief_iter_values)
    briefs = get_live_briefs_between_two_dates(
        data_api_client, "digital-specialists", date(2017, 3, 23), date(2017, 3, 23),
        'digital-outcomes-and-specialists-7',
    )
    assert data_api_client.find_briefs_iter.call_args_list == [
        mock.call(status="live", lot="digital-specialists", human=True, framework='digital-outcomes-and-specialists-7')
    ]
    assert briefs == [
        {"publishedAt": "2017-03-23T23:59:59.669156Z"},
        {"publishedAt": "2017-03-23T09:52:17.669156Z"},
        {"publishedAt": "2017-03-23T00:00:00.000000Z"}
    ]

    data_api_client.find_briefs_iter.return_value = iter(brief_iter_values)
    briefs = get_live_briefs_between_two_dates(
        data_api_client, "digital-specialists", date(2017, 3, 18), date(2017, 3, 20),
        'digital-outcomes-and-specialists-1',
    )
    assert briefs == [
        {"publishedAt": "2017-03-20T09:52:17.669156Z"},
        {"publishedAt": "2017-03-19T09:52:17.669156Z"},
        {"publishedAt": "2017-03-18T09:52:17.669156Z"}
    ]


ONE_BRIEF = [
    {
        "title": "Brief 1",
        "organisation": "the big SME",
        "location": "London",
        "applicationsClosedAt": "2016-07-05T23:59:59.000000Z",
        "id": "234",
        "lotName": "Digital specialists"
    },
]
MANY_BRIEFS = [
    {
        "title": "Brief 1",
        "organisation": "the big SME",
        "location": "London",
        "applicationsClosedAt": "2016-07-05T23:59:59.000000Z",
        "id": "234",
        "lotName": "Digital specialists"
    },
    {
        "title": "Brief 2",
        "organisation": "ministry of weird steps",
        "location": "Manchester",
        "applicationsClosedAt": "2016-07-07T23:59:59.000000Z",
        "id": "235",
        "lotName": "Digital specialists"
    }
]


def test_get_html_content_renders_brief_information():
    with freeze_time('2017-04-19 08:00:00'):
        html_content = get_html_content(ONE_BRIEF, 1)["html"]
        doc = html.fromstring(html_content)

        assert doc.xpath('//*[@class="opportunity-title"]')[0].text_content() == ONE_BRIEF[0]["title"]
        assert doc.xpath('//*[@class="opportunity-organisation"]')[0].text_content() == ONE_BRIEF[0]["organisation"]
        assert doc.xpath('//*[@class="opportunity-location"]')[0].text_content() == ONE_BRIEF[0]["location"]
        assert doc.xpath('//*[@class="opportunity-closing"]')[0].text_content() == "Closing Tuesday 5 July 2016"
        assert doc.xpath('//a[@class="opportunity-link"]')[0].text_content() == "https://www.digitalmarketplace.service.gov.uk/digital-outcomes-and-specialists/opportunities/234?utm_id=20170419"  # noqa


def test_get_html_content_renders_multiple_briefs():
    html_content = get_html_content(MANY_BRIEFS, 1)["html"]
    doc = html.fromstring(html_content)
    brief_titles = doc.xpath('//*[@class="opportunity-title"]')

    assert "2 new digital specialists opportunities were published" in html_content
    assert "View and apply for these opportunities:" in html_content

    assert len(brief_titles) == 2
    assert brief_titles[0].text_content() == "Brief 1"
    assert brief_titles[1].text_content() == "Brief 2"


def test_get_html_content_renders_singular_for_single_brief():
    html_content = get_html_content(ONE_BRIEF, 1)["html"]
    doc = html.fromstring(html_content)
    brief_titles = doc.xpath('//*[@class="opportunity-title"]')

    assert "1 new digital specialists opportunity was published" in html_content
    assert "View and apply for this opportunity:" in html_content

    assert len(brief_titles) == 1
    assert brief_titles[0].text_content() == "Brief 1"


def test_get_html_content_with_briefs_from_last_day():
    html_content = get_html_content(ONE_BRIEF, 1)["html"]
    assert "In the last day" in html_content


def test_get_html_content_with_briefs_from_several_days():
    with freeze_time('2017-04-17 08:00:00'):
        html_content = get_html_content(ONE_BRIEF, 3)["html"]
        assert "Since Friday" in html_content


def test_get_campaign_data():
    framework_name = "Digit Outcomes and Specialists Two"
    lot_name = "Digital Somethings"
    list_id = "1111111"

    with freeze_time('2017-04-19 08:00:00'):
        campaign_data = get_campaign_data(lot_name, list_id, framework_name)
        assert campaign_data["recipients"]["list_id"] == list_id
        assert campaign_data["settings"]["subject_line"] == f"New opportunities for {lot_name}: {framework_name}"
        assert campaign_data["settings"]["title"] == f"DOS Suppliers: {lot_name} [19 April]"
        assert campaign_data["settings"]["from_name"] == "Digital Marketplace Team"
        assert campaign_data["settings"]["reply_to"] == "do-not-reply@digitalmarketplace.service.gov.uk"


@pytest.mark.parametrize(
    ('framework_name'), ('Digital Outcomes and Specialists 2', 'Digital Outcomes and Specialists 3')
)
@mock.patch('dmscripts.send_dos_opportunities_email.get_html_content', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.get_campaign_data', autospec=True)
def test_main_creates_campaign_sets_content_and_sends_campaign(
    get_campaign_data, get_live_briefs_between_two_dates, get_html_content, framework_name
):
    live_briefs = [
        {"brief": "yaytest", "frameworkName": framework_name},
    ]
    get_live_briefs_between_two_dates.return_value = live_briefs
    get_campaign_data.return_value = {"created": "campaign"}
    get_html_content.return_value = {"first": "content"}

    dm_mailchimp_client = mock.MagicMock(spec=DMMailChimpClient)
    dm_mailchimp_client.create_campaign.return_value = "1"
    main(mock.MagicMock(), dm_mailchimp_client, LOT_DATA, 1, framework_name)

    # Creates campaign
    get_campaign_data.assert_called_once_with("Digital specialists", "096e52cebb", framework_name)
    dm_mailchimp_client.create_campaign.assert_called_once_with({"created": "campaign"})

    # Sets campaign content
    get_html_content.assert_called_once_with(live_briefs, 1)
    dm_mailchimp_client.set_campaign_content.assert_called_once_with("1", {"first": "content"})

    # Sends campaign
    dm_mailchimp_client.send_campaign.assert_called_once_with("1")


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
def test_main_gets_live_briefs_for_one_day(get_live_briefs_between_two_dates):
    with freeze_time('2017-04-19 08:00:00'):
        main(mock.MagicMock(), mock.MagicMock(), LOT_DATA, 1, 'Digital Outcomes and Specialists')
        get_live_briefs_between_two_dates.assert_called_once_with(
            mock.ANY, "digital-specialists", date(2017, 4, 18), date(2017, 4, 18), 'Digital Outcomes and Specialists'
        )


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
def test_main_gets_live_briefs_for_three_days(get_live_briefs_between_two_dates):
    with freeze_time('2017-04-10 08:00:00'):
        main(mock.MagicMock(), mock.MagicMock(), LOT_DATA, 3, 'Digital Outcomes and Specialists')
        get_live_briefs_between_two_dates.assert_called_once_with(
            mock.ANY, "digital-specialists", date(2017, 4, 7), date(2017, 4, 9), 'Digital Outcomes and Specialists'
        )


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
def test_if_no_briefs_then_no_campaign_created_nor_sent(get_live_briefs_between_two_dates, logger):
    get_live_briefs_between_two_dates.return_value = []

    dm_mailchimp_client = mock.MagicMock(DMMailChimpClient)
    result = main(mock.MagicMock(), dm_mailchimp_client, LOT_DATA, 3, 'Digital Outcomes and Specialists')

    assert result is True
    assert dm_mailchimp_client.create_campaign.call_count == 0
    assert dm_mailchimp_client.set_campaign_content.call_count == 0
    assert dm_mailchimp_client.send_campaign.call_count == 0

    logger.info.assert_called_with(
        "No new briefs found for 'digital-specialists' lot", extra={"number_of_days": 3}
    )
