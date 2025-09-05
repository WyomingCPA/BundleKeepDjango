from django.db import models

from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Product(models.Model):
    PRODUCT_TYPES = [
        ("own", "Собственный товар"),
        ("dropshipping", "Дропшиппинг"),
    ]
    
    
    name = models.CharField(max_length=200, verbose_name="Название")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена продажи")
    stock = models.PositiveIntegerField(default=0, help_text="Остаток на складе")
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Себестоимость")
    description = models.TextField(blank=True, verbose_name="Описание")
    created_at = models.DateTimeField(auto_now_add=True)
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        default="own"
    )
    supplier_url = models.URLField(blank=True, null=True, help_text="Ссылка на сайт поставщика")
    competitor_url = models.URLField(blank=True, null=True, help_text="Ссылка на сайт конкурента")
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Цена у конкурента")
    
    def profit(self):
        """Маржа с одной единицы"""
        return round(self.price - self.cost, 2)

    def margin_percent(self):
        """Рентабельность (%)"""
        if self.cost > 0:
            return round((self.price - self.cost) / self.cost * 100, 2)
        return 0
    
    def price_diff(self):
        """Разница с конкурентом (может быть отрицательной, если у нас дороже)"""
        if self.competitor_price is not None:
            return self.price - self.competitor_price
        return None
    price_diff.short_description = "Разница с конкурентом"

    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"


class Bundle(models.Model):
    name = models.CharField(max_length=200, verbose_name="Комплект")
    products = models.ManyToManyField(Product, related_name="bundles", verbose_name="Товары в комплекте")
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)")

    def total_price(self):
        """Итоговая цена с учётом скидки"""
        total = sum(product.price for product in self.products.all())
        if self.discount > 0:
            total = total * (100 - self.discount) / 100
        return round(total, 2)

    def total_cost(self):
        """Себестоимость комплекта"""
        return round(sum(product.cost for product in self.products.all()), 2)

    def profit(self):
        """Прибыль (цена - себестоимость)"""
        return round(self.total_price() - self.total_cost(), 2)

    def margin_percent(self):
        """Маржа (%)"""
        cost = self.total_cost()
        if cost > 0:
            return round((self.total_price() - cost) / cost * 100, 2)
        return 0

    def __str__(self):
        return self.name