from datetime import datetime, date
from django.core.exceptions import FieldError
from django_filters.rest_framework import FilterSet, NumberFilter, BaseInFilter, CharFilter
from orders.models import Line

class IntegerListFilter(BaseInFilter, NumberFilter):
    pass

class ListFilter(BaseInFilter, CharFilter):
    pass

class LineFilter(FilterSet):
    order_by_field = 'order_by'
    id = IntegerListFilter(field_name='id', lookup_expr='in')
    sales_order_number = ListFilter(field_name='sales_order_number', lookup_expr='in')
    purchase_order_number = ListFilter(field_name='sales_order_number', lookup_expr='in')
    item_number = CharFilter(field_name='item_number', lookup_expr='icontains')
    buyer = ListFilter(field_name='buyer__code', lookup_expr='in')
    planner = ListFilter(field_name='planner__code', lookup_expr='in')
    note = CharFilter(field_name='note', lookup_expr='icontains')
    confirmed_shipping_lt = NumberFilter(field_name='confirmed_shipping', lookup_expr='lt', method='filter_datetime_lt')
    confirmed_shipping_lte = NumberFilter(field_name='confirmed_shipping', lookup_expr='lte', method='filter_datetime_lte')
    confirmed_shipping_gt = NumberFilter(field_name='confirmed_shipping', lookup_expr='gt', method='filter_datetime_gt')
    confirmed_shipping_gte = NumberFilter(field_name='confirmed_shipping', lookup_expr='gte', method='filter_datetime_gte')

    class Meta:
        order_by_field = 'order_by'

    def datetime_from_epoch(self, value):
        return datetime.utcfromtimestamp(float(value))

    def filter_datetime(self, queryset, name, value, lookup):
        try:
            queryset = queryset.filter(**{lookup: self.datetime_from_epoch(value)})

        except (FieldError, ValueError):
            pass

        return queryset

    def filter_datetime_lt(self, queryset, name, value):
        lookup = '__'.join((name, 'lt',))
        return self.filter_datetime(queryset, name, value, lookup)

    def filter_datetime_lte(self, queryset, name, value):
        lookup = '__'.join((name, 'lte',))
        return self.filter_datetime(queryset, name, value, lookup)

    def filter_datetime_gt(self, queryset, name, value):
        lookup = '__'.join((name, 'gt',))
        return self.filter_datetime(queryset, name, value, lookup)

    def filter_datetime_gte(self, queryset, name, value):
        lookup = '__'.join((name, 'gte',))
        return self.filter_datetime(queryset, name, value, lookup)
