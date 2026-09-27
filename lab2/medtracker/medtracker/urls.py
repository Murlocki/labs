from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "MedTracker — администрирование"
admin.site.site_title = "MedTracker"
admin.site.index_title = "Управление системой"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("analyses.urls")),
]
