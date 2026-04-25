# from django.contrib import admin
# from .models import Feedback

# @admin.register(Feedback)
# class FeedbackAdmin(admin.ModelAdmin):
#     list_display = ('user', 'message', 'created_at')
from django.contrib import admin
from .models import Feedback
from .models import Profile
from .models import ScanHistory
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age')

@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
    list_display = ("url", "result", "probability", "user", "created_at")
    list_filter = ("result", "created_at", "user")
    search_fields = ("url", "user__username")
    ordering = ("-created_at",)

    # list_display = ('url', 'result', 'user', 'scanned_at')
    # search_fields = ('url', 'user__username')
    # list_filter = ('result',)

# admin.site.register(ScanHistory, ScanHistoryAdmin)

class CustomAdminSite(admin.AdminSite):
    site_header = "PhishTitan Admin Dashboard"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('url-stats/', self.admin_view(self.url_stats_view), name="url-stats"),
        ]
        return custom_urls + urls

    def url_stats_view(self, request):
        safe_urls = ScanHistory.objects.filter(result="safe") \
                        .values("url") \
                        .annotate(user_count=Count("user")) \
                        .order_by("-user_count")

        phishing_urls = ScanHistory.objects.filter(result="phishing") \
                        .values("url") \
                        .annotate(user_count=Count("user")) \
                        .order_by("-user_count")

        context = dict(
            self.each_context(request),
            safe_urls=safe_urls,
            phishing_urls=phishing_urls,
        )
        return TemplateResponse(request, "admin/url_stats.html", context)

# use custom admin site
custom_admin_site = CustomAdminSite(name="custom_admin")
