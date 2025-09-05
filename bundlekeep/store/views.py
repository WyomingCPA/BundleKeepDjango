from django.shortcuts import render

from django.shortcuts import render
from .models import Product, Bundle

def product_list(request):
    products = Product.objects.all()
    bundles = Bundle.objects.all()
    return render(request, "store/product_list.html", {
        "products": products,
        "bundles": bundles,
    })
