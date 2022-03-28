import pytz
from datetime import datetime, timedelta
from dateutil import tz
from django.http.request import QueryDict
from orders.filters import LineFilter


def generate_summary_context(feed=None):
    buyers = feed.get_distinct_buyers()
    summary = {}
    for entry in feed.summary.all():
        try:
            summary[entry.start_date]['summary'][entry.buyer.code] = {'quantity': entry.quantity, 'extended_quantity': entry.extended_quantity}

        except KeyError:
            summary[entry.start_date] = {
                'start_date': entry.start_date.strftime('%m/%d/%Y'),
                'end_date': (entry.start_date + timedelta(days=6)).strftime('%m/%d/%Y'),
                'summary': {buyer.code: {'quantity': 0, 'extended_quantity': 0} for buyer in buyers},
            }
            summary[entry.start_date]['summary'][entry.buyer.code]['quantity'] = entry.quantity
            summary[entry.start_date]['summary'][entry.buyer.code]['extended_quantity'] = entry.extended_quantity

    return {
        'uploaded_by': f'{feed.uploaded_by.first_name} {feed.uploaded_by.last_name}',
        'uploaded_at': feed.created_at.astimezone(tz.gettz('America/Hermosillo')).strftime('%m/%d/%Y %H:%m:%S'),
        'summary': summary,
    }

def generate_orders_export(feed=None, query_params={}):
    lines = LineFilter(QueryDict(query_string=query_params.urlencode()), queryset=feed.lines.all()).qs
    params = {key: value[0] if len(value) == 1 else value for key, value in query_params.items()}
    return {
        'lines': lines,
        'params': params,
    }
