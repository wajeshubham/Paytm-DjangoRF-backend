from django.db import models
# Create your models here.

class Order(models.Model):
    user_email=models.CharField(max_length=100)
    product_name = models.CharField(max_length=100)
    order_amount = models.CharField(max_length=25)
    isPaid = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name