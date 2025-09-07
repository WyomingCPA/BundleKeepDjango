from django.contrib import admin
from .models import Product, Bundle, Category, Sale, SaleItem, BundleItem, SaleBundleItem, AvitoAd, City
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class BundleItemInline(admin.TabularInline):
    model = BundleItem
    extra = 1


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "date", "customer_name", "total_amount")
    inlines = [SaleItemInline]

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
    
    readonly_fields = ("description_with_copy",)
    
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
    
    def description_with_copy(self, obj):
        if not obj.description:
            return "-"
        return mark_safe(f"""
            <textarea id="desc_{obj.id}" style="width:100%; height:120px;">{obj.description}</textarea>
            <button type="button" onclick="navigator.clipboard.writeText(document.getElementById('desc_{obj.id}').value)">
                📋 Скопировать
            </button>
        """)
    description_with_copy.short_description = "Описание"

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
    
    
class AvitoAdInline(admin.TabularInline):
    model = AvitoAd
    extra = 1
    fields = ('title', 'price', 'competitor_price', 'published', 'avito_url')
    readonly_fields = ('avito_url',)

    def avito_url(self, obj):
        if obj.avito_url:
            return f'<a href="{obj.avito_url}" target="_blank">{obj.avito_url}</a>'
        return "-"
    avito_url.allow_tags = True
    avito_url.short_description = "Avito ссылка"
    
@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(AvitoAd)
class AvitoAdAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'competitor_price', 'published')
    list_filter = ('published', 'cities')
    search_fields = ('title', 'description')
    filter_horizontal = ('cities',)