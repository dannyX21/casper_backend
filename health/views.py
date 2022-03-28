from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class HealthView(APIView):
    def get(self, request, format=None):
        return Response("pong", status=status.HTTP_200_OK)
