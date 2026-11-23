"""Date window tests for issue #8. Run: python -m pytest tests/"""
import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import common
from utils.common import apply_date_window, format_event_date, parse_event_date

TODAY = date(2026, 11, 23)


def ev(title, dt, category='STEM / Factual', source='UCL East', **kw):
    e = {'title': title, 'date_obj': dt, 'date_str': 'RAW', 'category': category, 'source': source}
    e.update(kw)
    return e


def titles(result):
    return [e['title'] for e in result.kept]


def test_future_in_window_is_kept_and_reformatted():
    r = apply_date_window([ev('Talk', datetime(2026, 11, 25, 18, 15, tzinfo=timezone.utc))], TODAY)
    assert titles(r) == ['Talk']
    assert r.kept[0]['date_str'] == 'Wed, 25 Nov 2026 @ 18:15'


def test_today_is_kept_past_day_is_dropped():
    r = apply_date_window([ev('Today', datetime(2026, 11, 23, 0, 0)),
                           ev('Yesterday', datetime(2026, 11, 22, 23, 0))], TODAY)
    assert titles(r) == ['Today']
    assert r.dropped_past == 1


def test_far_future_event_is_dropped():
    # UCL East row from the issue: Wed, 10 Feb 2027 (11 weeks ahead)
    r = apply_date_window([ev('Explore your entrepreneurial idea', datetime(2027, 2, 10, 14, 0))], TODAY)
    assert r.kept == []
    assert r.dropped_later == 1


def test_horizon_is_one_named_constant():
    edge = datetime(2027, 1, 18, 12, 0)  # exactly today + 8 weeks
    assert titles(apply_date_window([ev('Edge', edge)], TODAY)) == ['Edge']
    over = datetime(2027, 1, 19, 12, 0)
    assert apply_date_window([ev('Over', over)], TODAY).kept == []
    assert common.REPORT_HORIZON_WEEKS == 8


def test_raw_feed_timestamp_news_row_is_dropped_when_stale():
    # Dining row from the issue: Tue, 29 Sep 2026 07:00:00 GMT, 55 days old
    raw = datetime.strptime('Tue, 29 Sep 2026 07:00:00 GMT', '%a, %d %b %Y %H:%M:%S %Z')
    r = apply_date_window([ev('Westfield boss', raw, category='Dining & Offers', source='Google News',
                              date_str='Tue, 29 Sep 2026 07:00:00 GMT')], TODAY)
    assert r.kept == []
    assert r.dropped_stale_news == 1


def test_recent_news_kept_with_standard_date_format():
    raw = datetime.strptime('Sat, 21 Nov 2026 09:15:00 GMT', '%a, %d %b %Y %H:%M:%S %Z')
    r = apply_date_window([ev('QEOP news', raw, category='News & Alerts', source='Google News',
                              date_str='Sat, 21 Nov 2026 09:15:00 GMT')], TODAY)
    assert r.kept[0]['date_str'] == 'Sat, 21 Nov 2026 @ 09:15'
    assert 'GMT' not in r.kept[0]['date_str']


def test_rows_without_title_are_not_printed_and_are_counted():
    r = apply_date_window([ev('', datetime(2026, 11, 25, 9, 0)),
                           ev(None, datetime(2026, 11, 25, 9, 0)),
                           ev('   ', datetime(2026, 11, 25, 9, 0))], TODAY)
    assert r.kept == []
    assert r.dropped_untitled == 3


def test_midnight_has_no_time_suffix():
    assert format_event_date(datetime(2026, 11, 27, 0, 0)) == 'Fri, 27 Nov 2026'


def test_outcome_pass():
    r = apply_date_window([ev('A', datetime(2026, 11, 25, 9, 0))], TODAY)
    assert r.check() == ('PASS', [])


def test_outcome_indeterminate_names_the_source():
    r = apply_date_window([ev('A', datetime(2026, 11, 25, 9, 0)),
                           ev('B', None, source='Sadler\'s Wells')], TODAY)
    outcome, details = r.check()
    assert outcome == 'INDETERMINATE'
    assert "Sadler's Wells" in details[0]


def test_outcome_fail_lists_rows_outside_window():
    r = apply_date_window([ev('A', datetime(2026, 11, 25, 9, 0))], TODAY)
    r.kept.append(ev('Leaked', datetime(2027, 3, 1, 9, 0)))  # simulate a leak
    outcome, details = r.check()
    assert outcome == 'FAIL'
    assert 'Leaked' in details[0]


def test_parse_event_date_iso_and_fuzzy():
    # was a NameError (date_raw) swallowed by a bare except
    assert parse_event_date('2026-11-25T18:15:00') == datetime(2026, 11, 25, 18, 15)
    assert parse_event_date('25 Nov 2026') == datetime(2026, 11, 25)
    assert parse_event_date('see website') is None
