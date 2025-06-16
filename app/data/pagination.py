from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class Pagination(PageNumberPagination):
    """Species Pagination"""
    page_query_param = 'page'
    page_size = 20

    def paginate_queryset(self, queryset, request, view=None):
        page_param = request.query_params.get(self.page_query_param, '1')

        if '-' in page_param:
            try:
                start, end = map(int, page_param.split('-'))
                if start < 1 or end < start:
                    return []
                start_index = (start - 1) * self.page_size
                end_index = end * self.page_size
                self.page = queryset[start_index:end_index]  # ✅ FIXED
                return self.page
            except ValueError:
                return []
        else:
            return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if hasattr(self, 'page') and self.page is not None:
            return super().get_paginated_response(data)
        else:
            return Response({
                "count": len(data),
                "results": data
            })
