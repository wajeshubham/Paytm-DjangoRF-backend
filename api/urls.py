from django.urls import path
from .views import *

urlpatterns = [
    path('pay/',start_payment,name="start_payment"),
    path('handlepayment/',handlepayment,name="handlepayment"),
]