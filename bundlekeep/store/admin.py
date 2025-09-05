from django.contrib import admin
from .models import Product, Bundle, Category
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "price", "cost", "profit_display", "competitor_price", "colored_price_diff", 
        "margin_display", "supplier_link", "competitor_link", "created_at")
    list_filter = ("product_type", "category")  # фильтрация/сортировка в админке
    search_fields = ("name",)
    
    def profit_display(self, obj):
        return f"{obj.profit()} ₽"
    profit_display.short_description = "Прибыль"

    def margin_display(self, obj):
        return f"{obj.margin_percent()} %"
    margin_display.short_description = "Маржа %"
    
    def supplier_link(self, obj):
        if obj.supplier_url:
            return format_html('<a href="{}" target="_blank">Поставщик</a>', obj.supplier_url)
        return "-"
    supplier_link.short_description = "Сайт поставщика"

    def competitor_link(self, obj):
        if obj.competitor_url:
            return format_html('<a href="{}" target="_blank">Конкурент</a>', obj.competitor_url)
        return "-"
    competitor_link.short_description = "Сайт конкурента"
    
    def colored_price_diff(self, obj):
        diff = obj.price_diff()
        if diff is None:
            return "-"
        if diff < 0:  # у нас дешевле
            color = "green"
        elif diff > 0:  # у нас дороже
            color = "red"
        else:
            color = "gray"
        return format_html('<span style="color: {};">{} ₽</span>', color, diff)

    colored_price_diff.short_description = "Разница с конкурентом"


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ("name", "discount", "total_price_display", "total_cost_display", "profit_display", "margin_display")

    def total_price_display(self, obj):
        return f"{obj.total_price()} ₽"
    total_price_display.short_description = "Цена продажи"

    def total_cost_display(self, obj):
        return f"{obj.total_cost()} ₽"
    total_cost_display.short_description = "Себестоимость"

    def profit_display(self, obj):
        return f"{obj.profit()} ₽"
    profit_display.short_description = "Прибыль"

    def margin_display(self, obj):
        return f"{obj.margin_percent()} %"
    margin_display.short_description = "Маржа %"