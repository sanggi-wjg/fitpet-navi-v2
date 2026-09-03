from datetime import datetime

import pytz
from freezegun import freeze_time

from fitpet_navi.util.util_datetime import get_utc_now


@freeze_time("2025-09-05 11:37:46", tz_offset=0)
def test_get_utc_now():
    # given
    expected = datetime(2025, 9, 5, 11, 37, 46, tzinfo=pytz.UTC)

    # when / then
    result = get_utc_now()

    assert result == expected
