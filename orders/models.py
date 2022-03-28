import hashlib
import uuid
from base64 import b64encode
from django.template.loader import render_to_string
from easy_pdf.rendering import render_to_pdf
from django.db import models
from orders.tasks import generate_summary_context, generate_orders_export


def get_uuid_filename(_, filename):
    return f'feeds/{uuid.uuid4()}/{filename}'


def get_file_checksum(src):
    if src:
        hash_md5 = hashlib.md5()
        for chunk in src.chunks(4096):
            hash_md5.update(chunk)

        return hash_md5.hexdigest()

    return None


class Feed(models.Model):
    file = models.FileField(upload_to=get_uuid_filename,
                            null=False, blank=False)
    filename = models.CharField(max_length=255, blank=False, null=False)
    uploaded_by = models.ForeignKey(
        'users.User', null=True, blank=True, on_delete=models.CASCADE)
    summary_export = models.TextField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'feeds'
        ordering = ['id', ]

    def get_file_url(self):
        return self.file.url

    def get_md5_checksum(self):
        return get_file_checksum(self.file)

    def get_distinct_buyers(self):
        buyer_ids = self.lines.all().order_by('buyer').values_list('buyer', flat=True).distinct()
        return Buyer.objects.filter(id__in=buyer_ids)

    def get_distinct_planners(self):
        planner_ids = self.lines.all().order_by('planner').values_list('planner', flat=True).distinct()
        return Planner.objects.filter(id__in=planner_ids)

    def get_summary_export(self):
        if self.summary_export is None:
            ctx = generate_summary_context(feed=self)
            pdf_bytes = render_to_pdf('reports/summary.html', ctx)
            self.summary_export = b64encode(pdf_bytes).decode('ascii')
            self.save()

        return self.summary_export

    def get_orders_export(self, query_params=''):
        ctx = generate_orders_export(feed=self, query_params=query_params)
        pdf_bytes = render_to_pdf('reports/orders.html', ctx)
        orders_export = b64encode(pdf_bytes).decode('ascii')
        return orders_export

    def __str__(self):
        return self.filename


class Line(models.Model):
    class Meta:
        ordering = ['id', ]

    feed = models.ForeignKey('orders.Feed', null=False,
                             blank=False, on_delete=models.CASCADE, related_name='lines')
    sales_order_number = models.CharField(
        max_length=16, null=False, blank=False)
    item_number = models.CharField(max_length=32, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=False)
    extended_quantity = models.PositiveIntegerField(null=False, blank=False)
    unit = models.CharField(max_length=8, null=False,
                            blank=False, default='pcs')
    requested_receipt = models.DateField(null=True, blank=True, default=None)
    requested_shipping = models.DateField(null=True, blank=True, default=None)
    confirmed_shipping = models.DateField(null=True, blank=True, default=None)
    note = models.TextField(null=True, blank=True, default=None)
    site = models.CharField(max_length=16, null=False,
                            blank=False, default='104-CA')
    ship_to_name = models.CharField(max_length=128, null=True, blank=True)
    unit_price = models.DecimalField(
        null=False, blank=False, max_digits=8, decimal_places=2)
    net_amount = models.DecimalField(
        null=False, blank=False, max_digits=10, decimal_places=2)
    customer_reference = models.CharField(
        max_length=128, null=True, blank=True)
    buyer = models.ForeignKey(
        'orders.Buyer', null=False, blank=False, on_delete=models.CASCADE, related_name='lines')
    planner = models.ForeignKey(
        'orders.Planner', null=False, blank=False, on_delete=models.CASCADE, related_name='lines')
    sales_taker = models.CharField(max_length=64, null=False, blank=False)
    purchase_order_number = models.CharField(
        max_length=64, null=False, blank=False)
    original_commit_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(null=False, blank=False)
    updated_at = models.DateTimeField(null=False, blank=False)
    revision = models.CharField(max_length=8, null=False, blank=False)


class Buyer(models.Model):
    class Meta:
        ordering = ['code']

    code = models.CharField(max_length=16, null=False, blank=False)
    name = models.CharField(max_length=64, null=True, blank=False)

    def __str__(self):
        return f'{self.id}: {self.code} ({self.name})'


class Planner(models.Model):
    class Meta:
        ordering = ['code']

    code = models.CharField(max_length=16, null=False, blank=False)
    name = models.CharField(max_length=64, null=True, blank=False)

    def __str__(self):
        return f'{self.id}: {self.code} ({self.name})'


class Summary(models.Model):
    class Meta:
        ordering = ['feed__id', 'start_date', ]
    feed = models.ForeignKey('orders.Feed', null=False,
                             blank=False, related_name='summary', on_delete=models.CASCADE)
    buyer = models.ForeignKey(
        'orders.Buyer', null=False, blank=False, on_delete=models.CASCADE)
    start_date = models.DateField(null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=False, default=0)
    extended_quantity = models.PositiveIntegerField(
        null=False, blank=False, default=0)
