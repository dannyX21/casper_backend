from django.urls import path, include
from rest_framework_nested import routers
from orders.views import OrderView, FeedView, SummaryView, BuyerView, PlannerView

router = routers.SimpleRouter()
router.register(r'orders', OrderView, basename='orders')
router.register(r'feeds', FeedView, basename='feeds')
router.register(r'buyers', BuyerView, basename='buyers')
router.register(r'planners', PlannerView, basename='planners')

feeds_router = routers.NestedSimpleRouter(router, r'feeds', lookup='feed')
feeds_router.register(r'orders', OrderView)
feeds_router.register(r'summary', SummaryView)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(feeds_router.urls)),
]
