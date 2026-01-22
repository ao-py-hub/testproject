from django.contrib import admin
from .models import Gacha, Prize

@admin.register(Gacha)
class GachaAdmin(admin.ModelAdmin):
    list_display = ("title", "public_id", "owner", "is_public", "created_at")
    search_fields = ("title", "public_id", "owner__username")
    list_filter = ("is_public", "created_at")

@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ("name", "gacha", "weight", "stock_remaining", "sort_order")
    search_fields = ("name", "gacha__title", "gacha__public_id")
    list_filter = ("gacha",)