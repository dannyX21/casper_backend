import hashlib
import uuid
from django.db import models


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
    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'feeds'
        ordering = ['id', ]

    def get_file_url(self):
        return self.file.url

    def get_md5_checksum(self):
        return get_file_checksum(self.file)

    def __str__(self):
        return self.filename


class Line(models.Model):
    class Meta:
        ordering = ['id', ]

    feed = models.ForeignKey('orders.Feed', null=False,
                             blank=False, on_delete=models.CASCADE)
    sales_order_number = models.CharField(
        max_length=10, null=False, blank=False)
    item_number = models.CharField(max_length=32, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=False)
    extended_quantity = models.PositiveIntegerField(null=False, blank=False)
    unit = models.CharField(max_length=8, null=False,
                            blank=False, default='pcs')
    requested_receipt = models.DateField(null=True, blank=True, default=None)
    requested_shipping = models.DateField(null=True, blank=True, default=None)
    confirmed_shipping = models.DateField(null=True, blank=True, default=None)
    note = models.TextField(null=True, blank=True, default=None)
    site = models.CharField(max_length=8, null=False,
                            blank=False, default='104-CA')
    ship_to_name = models.CharField(max_length=128, null=True, blank=True)
    unit_price = models.DecimalField(
        null=False, blank=False, max_digits=8, decimal_places=2)
    net_amount = models.DecimalField(
        null=False, blank=False, max_digits=10, decimal_places=2)
    customer_reference = models.CharField(
        max_length=128, null=True, blank=True)
    buyer = models.ForeignKey(
        'orders.Buyer', null=False, blank=False, on_delete=models.CASCADE)
    planner = models.ForeignKey(
        'orders.Planner', null=False, blank=False, on_delete=models.CASCADE)
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
                             blank=False, on_delete=models.CASCADE)
    buyer = models.ForeignKey(
        'orders.Buyer', null=False, blank=False, on_delete=models.CASCADE)
    start_date = models.DateField(null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=False, default=0)
    extended_quantity = models.PositiveIntegerField(
        null=False, blank=False, default=0)
