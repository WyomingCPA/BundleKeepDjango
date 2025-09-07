from django.db import models

from django.db import models
from django.utils import timezone

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
    
class Sale(models.Model):
    date = models.DateTimeField(default=timezone.now)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"

    def __str__(self):
        return f"Продажа #{self.id} от {self.date.strftime('%Y-%m-%d')}"

    def calculate_total(self):
        total = sum(item.total_price() for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, blank=True, null=True)
    bundle = models.ForeignKey(Bundle, on_delete=models.PROTECT, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        if self.product:
            return f"{self.product.name} x{self.quantity}"
        elif self.bundle:
            return f"Комплект: {self.bundle.name} x{self.quantity}"
        return "Неизвестный товар"

    def total_price(self):
        return self.price_at_sale * self.quantity

    def save(self, *args, **kwargs):
        if self.pk is None:  # новая строка продажи
            if self.product:
                if self.product.stock is not None:
                    self.product.stock = max(0, self.product.stock - self.quantity)
                    self.product.save()
            elif self.bundle:
                # уменьшаем остатки по каждому товару внутри комплекта
                for item in self.bundle.items.all():
                    if item.product.stock is not None:
                        item.product.stock = max(0, item.product.stock - item.quantity * self.quantity)
                        item.product.save()
        super().save(*args, **kwargs)

class SaleBundleItem(models.Model):
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name='bundle_items')
    bundle = models.ForeignKey(Bundle, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.pk:
            # проверяем остатки
            for bundle_item in self.bundle.bundle_items.all():
                required = bundle_item.quantity * self.quantity
                if bundle_item.product.stock < required:
                    raise ValueError(
                        f"Недостаточно {bundle_item.product.name}: нужно {required}, есть {bundle_item.product.stock}"
                    )
            # уменьшаем остатки
            for bundle_item in self.bundle.bundle_items.all():
                required = bundle_item.quantity * self.quantity
                bundle_item.product.stock -= required
                bundle_item.product.save()
        super().save(*args, **kwargs)
        
class BundleItem(models.Model):
    bundle = models.ForeignKey(Bundle, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
class City(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class AvitoAd(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # ссылка на товар или комплект
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='avito_ads'
    )
    bundle = models.ForeignKey(
        Bundle, on_delete=models.SET_NULL, null=True, blank=True, related_name='avito_ads'
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)
    competitor_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # города, где публикуем
    cities = models.ManyToManyField(City, related_name='avito_ads')

    # статусы публикации
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)

    # ссылки
    avito_url = models.URLField(blank=True, null=True)
    supplier_url = models.URLField(blank=True, null=True)
    competitor_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({'товар' if self.product else 'комплект'})"