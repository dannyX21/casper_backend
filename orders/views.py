import re
from base64 import b64encode
from datetime import datetime, timedelta
from decimal import Decimal
from easy_pdf.rendering import render_to_pdf
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import dateparse
from rest_framework import mixins, viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from orders.models import Line, Buyer, Planner, Summary, Feed
from orders.serializers import FeedSerializer, LineSerializer, LineShortSerializer, \
    SummarySerializer, BuyerSerializer, PlannerSerializer
from orders.filters import LineFilter
from orders.tasks import generate_summary_context

kit_re = re.compile(r'^EZ(?:C5E|C6|C6A|RD6|FP[RS|PM](?:6A|5E|6))\d{2,3}Q(\d{2,3})-\d{2}$')


class FeedView(mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):

    serializer_class = FeedSerializer
    permission_classes = (IsAuthenticated,)
    model = Feed
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    ordering = ('-id')
    ordering_fields = '__all__'
    queryset = Feed.objects.all()

    def get_queryset(self):
        queryset = self.queryset.prefetch_related(
            'lines',
            'lines__buyer',
            'lines__planner',
            'uploaded_by',
        )
        return queryset

    def get_serializer_context(self):
        context = super(FeedView, self).get_serializer_context()
        context['user'] = self.request.user
        
        return context

    @action(methods=['post'], detail=False)
    def upload(self, request, **kwargs):
        if request.FILES.get('file') is None:
            return Response({'detail': 'A file is required!'}, status=status.HTTP_400_BAD_REQUEST)

        request.data['file'] = request.FILES['file']
        if request.data.get('filename'):
            request.FILES['file'].name = request.data.get('filename')

        else:
            request.data['filename'] = request.FILES['file'].name

        context = self.get_serializer_context()
        try:
            with transaction.atomic():
                serializer = FeedSerializer(data=request.data, many=False, context=context)
                serializer.is_valid(raise_exception=True)
                feed = serializer.create(serializer.validated_data)
                buyers = {buyer.code: buyer for buyer in Buyer.objects.all()}
                planners = {planner.code: planner for planner in Planner.objects.all()}
                try:
                    wb = load_workbook(feed.file.name, data_only=True)

                except InvalidFileException:
                    return Response('Invalid File!', status=status.HTTP_400_BAD_REQUEST)
                
                summary_dict = {}
                ws = wb.worksheets[0]
                for (index, row) in enumerate(ws.rows):
                    site = row[11].value
                    confirmed_shipping = row[9].value
                    if site != '104-CA' or confirmed_shipping is None:
                        continue

                    quantity = int(float(row[5].value))
                    buyer_code = row[18].value
                    planner_code = row[19].value
                    item_number = row[2].value
                    if buyer_code == 'ORT':
                        m = kit_re.match(item_number)
                        if m is not None:
                            extended_quantity = quantity * int(m.group(1))

                        else:
                            extended_quantity = quantity

                    else:
                        extended_quantity = quantity

                    line = Line.objects.create(
                        sales_order_number = row[0].value,
                        item_number = item_number,
                        revision = row[4].value,
                        quantity = quantity,
                        extended_quantity = extended_quantity,
                        unit = row[6].value,
                        requested_receipt = row[7].value,
                        requested_shipping = row[8].value,
                        confirmed_shipping = confirmed_shipping,
                        note = row[10].value,
                        site = site,
                        ship_to_name = row[12].value,
                        unit_price = Decimal(row[15].value),
                        net_amount = Decimal(row[16].value),
                        customer_reference = row[17].value,
                        buyer = buyers[buyer_code],
                        planner = planners[planner_code] if planner_code is not None else planners[buyer_code],
                        sales_taker = row[20].value,
                        purchase_order_number = row[21].value,
                        original_commit_date = row[22].value,
                        created_at = row[23].value,
                        updated_at = row[24].value,
                        feed=feed
                    )
                    if line.confirmed_shipping is not None:
                        start_date = line.confirmed_shipping - timedelta(days=line.confirmed_shipping.weekday())
                        
                        try:
                            summary_dict[start_date][line.buyer]['quantity'] += quantity
                            summary_dict[start_date][line.buyer]['extended_quantity'] += extended_quantity

                        except KeyError as e:
                            if str(e).startswith('datetime'):
                                summary_dict[start_date] = {line.buyer: {'quantity': quantity, 'extended_quantity': extended_quantity}}

                            else:
                                summary_dict[start_date][line.buyer] = {'quantity': quantity, 'extended_quantity': extended_quantity}

                for (dt, s) in summary_dict.items():
                    for (b, d) in s.items():
                        Summary.objects.create(
                            feed=feed,
                            start_date=dt,
                            buyer=b,
                            quantity=d['quantity'],
                            extended_quantity=d['extended_quantity'],
                        )
        except Exception as e:
            return Response({'error': f'The following exception occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        feed_serializer = FeedSerializer(feed, many=False, context=context)
        return Response(feed_serializer.data, status=status.HTTP_201_CREATED)


class OrderView(mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    serializer_class = LineSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Line.objects.all()
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = LineFilter
    ordering_fields = ('sales_order_number', 'purchase_order_number', 'confirmed_shipping', 'item_number', 'note', 'buyer__code', 'planner__code',)
    ordering = ('id',)
    
    def get_serializer_context(self):
        context = super(OrderView, self).get_serializer_context()
        context['user'] = self.request.user
        if 'feed_pk' in self.kwargs:
            context['feed_pk'] = int(self.kwargs['feed_pk'])
            context['feed'] = get_object_or_404(Feed, pk=context['feed_pk'])

        return context

    def get_queryset(self):
        context = self.get_serializer_context()
        queryset = self.queryset
        if context.get('feed_pk') is not None:
            queryset = queryset.filter(feed__id=context['feed_pk'])

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return LineShortSerializer

        elif self.action == 'retrieve':
            return LineSerializer

        return self.serializer_class

    @action(detail=False, methods=('get',), url_path='export')
    def export(self, request, **kwargs):
        context = self.get_serializer_context()
        orders_export = context['feed'].get_orders_export(query_params=request.query_params)
        return Response({'report': orders_export}, status.HTTP_200_OK)


class SummaryView(mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    serializer_class = SummarySerializer
    permission_classes = (IsAuthenticated,)
    queryset = Summary.objects.all()
    ordering = ('start_date', 'buyer__code',)
    
    def get_serializer_context(self):
        context = super(SummaryView, self).get_serializer_context()
        context['user'] = self.request.user
        if 'feed_pk' in self.kwargs:
            context['feed_pk'] = int(self.kwargs['feed_pk'])
            context['feed'] = get_object_or_404(Feed, pk=context['feed_pk'])

        return context

    def get_queryset(self):
        context = self.get_serializer_context()
        queryset = self.queryset
        if context.get('feed_pk') is not None:
            queryset = queryset.filter(feed__id=context['feed_pk'])

        return queryset.order_by('start_date', 'buyer__code')

    @action(detail=False, methods=('get',), url_path='export')
    def export(self, request, **kwargs):
        context = self.get_serializer_context()
        summary_export = context['feed'].get_summary_export()
        return Response({'report': summary_export,}, status.HTTP_200_OK)


class BuyerView(mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    serializer_class = BuyerSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Buyer.objects.all()
    ordering = ('code',)


class PlannerView(mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet):
    serializer_class = PlannerSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Planner.objects.all()
    ordering = ('code',)
