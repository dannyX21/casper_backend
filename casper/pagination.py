from rest_framework.pagination import PageNumberPagination


class CasperPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 500

    def paginate_queryset(self, queryset, request, view=None):

        if request.query_params.get('pagination') == '0':
            super(CasperPagination, self).paginate_queryset(queryset, request, view)
            return list(queryset)

        return super(CasperPagination, self).paginate_queryset(queryset, request, view)

    def get_next_link(self):
        if self.request.query_params.get('pagination') == '0':
            return None

        return super(CasperPagination, self).get_next_link()

    def get_previous_link(self):
        if self.request.query_params.get('pagination') == '0':
            return None

        return super(CasperPagination, self).get_previous_link()
