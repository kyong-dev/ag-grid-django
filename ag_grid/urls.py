from django.urls import path

from ag_grid.api import AgGridCreateAPIView, AgGridDeleteAPIView, AgGridFormFieldsAPIView, AgGridHeaderAPIView, AgGridUpdateAPIView, AgGridFilteredListView

app_name = "ag-grid"

urlpatterns = [
    path("<str:app_label>/<str:model_name>/list-headers/", AgGridHeaderAPIView.as_view(), name="headers"),
    path("<str:app_label>/<str:model_name>/<int:pk>/update/", AgGridUpdateAPIView.as_view(), name="update"),
    path("<str:app_label>/<str:model_name>/create/", AgGridCreateAPIView.as_view(), name="create"),
    path("<str:app_label>/<str:model_name>/<int:pk>/delete/", AgGridDeleteAPIView.as_view(), name="delete"),
    path("<str:app_label>/<str:model_name>/form-fields/", AgGridFormFieldsAPIView.as_view(), name="form-fields"),
    path("<str:app_label>/<str:model_name>/filtered-data-source/", AgGridFilteredListView.as_view(), name="filtered-data-source"),
]
