from datetime import timedelta
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from orders.models import Feed, Line, Summary, Planner, Buyer
from users.serializers import UserSerializer

SUPPORTED_EXTENSIONS = {'xls', 'xlsx',}


class FeedSerializer(serializers.ModelSerializer):
    url = serializers.URLField(required=False, write_only=True)
    uploaded_by = serializers.SerializerMethodField()

    class Meta:
        model = Feed
        fields = (
            'id',
            'file',
            'filename',
            'url',
            'uploaded_by',
            'created_at',
            'updated_at',
        )

    def to_internal_value(self, data):
        internal_data = super(FeedSerializer, self).to_internal_value(data)
        internal_data['uploaded_by'] = self.context.get('user')
        return internal_data

    def validate(self, data):
        validated_data = super(FeedSerializer, self).validate(data)
        supported = False
        try:
            if validated_data['file'].name.split('.')[-1] in SUPPORTED_EXTENSIONS:
                supported = True

        except IndexError:
            pass

        if not supported:
            raise ValidationError(f'File not supported!, only the following extensions are supported: {", ".join(SUPPORTED_EXTENSIONS)}.')

        return validated_data

    def get_uploaded_by(self, instance):
        if instance.uploaded_by is not None:
            serializer = UserSerializer(instance.uploaded_by, many=False, context=self.context)
            return serializer.data

        return None


class LineSerializer(serializers.ModelSerializer):
    buyer = serializers.SerializerMethodField()
    planner = serializers.SerializerMethodField()

    class Meta:
        model = Line
        fields = (
            'id',
            'sales_order_number',
            'item_number',
            'revision',
            'quantity',
            'extended_quantity',
            'unit',
            'requested_receipt',
            'requested_shipping',
            'confirmed_shipping',
            'note',
            'site',
            'ship_to_name',
            'unit_price',
            'net_amount',
            'customer_reference',
            'buyer',
            'planner',
            'sales_taker',
            'purchase_order_number',
            'original_commit_date',
            'created_at',
            'updated_at',
        )
    def get_buyer(self, instance):
        if instance.buyer is not None:
            serializer = BuyerSerializer(instance.buyer, many=False, context=self.context)
            return serializer.data

        return None

    def get_planner(self, instance):
        if instance.planner is not None:
            serializer = PlannerSerializer(instance.planner, many=False, context=self.context)
            return serializer.data

        return None
    

class LineShortSerializer(LineSerializer):

    class Meta:
        model = Line
        fields = (
            'id',
            'sales_order_number',
            'item_number',
            'revision',
            'quantity',
            'extended_quantity',
            'unit',
            'confirmed_shipping',
            'note',
            'ship_to_name',
            'unit_price',
            'net_amount',
            'buyer',
            'planner',
            'purchase_order_number',
            'original_commit_date',
            'created_at',
            'updated_at',
        )


class PlannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planner
        fields = '__all__'


class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = '__all__'


class SummarySerializer(serializers.ModelSerializer):
    end_date = serializers.SerializerMethodField()
    buyer = serializers.SerializerMethodField()

    class Meta:
        model = Summary
        fields = (
            'id',
            'buyer',
            'start_date',
            'end_date',
            'quantity',
            'extended_quantity',
        )

    def get_end_date(self, instance):
        if instance.start_date is not None:
            return instance.start_date + timedelta(days=6)

        return None

    def get_buyer(self, instance):
        if instance.buyer is not None:
            serializer = BuyerSerializer(instance.buyer, many=False, context=self.context)
            return serializer.data

        return None
