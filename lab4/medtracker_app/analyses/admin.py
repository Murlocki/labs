from django.contrib import admin

from .models import Analysis, AnalysisValue, Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "note")
    list_filter = ("note",)
    search_fields = ("name",)


class AnalysisValueInline(admin.TabularInline):
    model = AnalysisValue
    extra = 0
    fields = ("value", "measured_at", "note")


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "unit", "created_at")
    list_filter = ("user", "unit")
    search_fields = ("name",)
    list_select_related = ("user", "unit")
    inlines = [AnalysisValueInline]


@admin.register(AnalysisValue)
class AnalysisValueAdmin(admin.ModelAdmin):
    list_display = ("analysis", "owner", "value", "measured_at", "note")
    list_filter = ("analysis__user", "measured_at")
    search_fields = ("analysis__name", "value", "note")
    list_select_related = ("analysis__user",)
    date_hierarchy = "measured_at"

    @admin.display(description="владелец", ordering="analysis__user__username")
    def owner(self, obj):
        return obj.analysis.user
