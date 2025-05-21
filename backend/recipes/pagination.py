from rest_framework.pagination import PageNumberPagination

"""
This module contains custom pagination settings for the API.
"""

class CustomPagination(PageNumberPagination):
    """Custom pagination class that defines pagination settings."""
    
    page_size = 6
    page_size_query_param = 'limit'
