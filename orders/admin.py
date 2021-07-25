from django.contrib import admin
from orders.models import Feed, Line, Buyer, Planner, Summary
# Register your models here.


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'uploaded_by', 'created_at',)
    raw_id_fields = ('uploaded_by',)


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ('id', 'feed', 'sales_order_number', 'purchase_order_number',
                    'item_number', 'quantity', 'confirmed_shipping', 'buyer', 'planner',)
    raw_id_fields = ('feed', 'buyer', 'planner',)
    search_fields = ('sales_order_number', 'item_number', 'purchase_order_number',
                     'customer_reference', 'buyer__code', 'planner__code',)


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    search_fields = ('code', 'name')


@admin.register(Planner)
class PlannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    search_fields = ('code', 'name')


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'feed', 'buyer', 'start_date', 'quantity', 'extended_quantity',)
    search_fields = ('buyer__code', 'buyer__name',)
    raw_id_fields = ('feed', 'buyer',)
