import environ

from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer
from . import Checksum

# Create your views here.

env = environ.Env()

# you have to create .env file in same folder where you are using environ.Env()
# reading .env file which located in api folder
environ.Env.read_env()


@api_view(['POST'])
def start_payment(request):
    # request.data is coming from frontend
    amount = request.data['amount']
    name = request.data['name']
    email = request.data['email']

    # we are saving an order with keeping isPaid=False
    order = Order.objects.create(product_name=name,
                                 order_amount=amount,
                                 user_email=email, )

    # in case if you want to use above order instance just serialize it
    serializer = OrderSerializer(order)

    # we have to send the param_dict to the frontend
    # these credentials will be passed to paytm order processor to verify the business account
    param_dict = {
        'MID': env('MERCHANTID'),
        'ORDER_ID': str(order.id),
        'TXN_AMOUNT': str(amount),
        'CUST_ID': email,
        'INDUSTRY_TYPE_ID': 'Retail',
        'WEBSITE': 'WEBSTAGING',
        'CHANNEL_ID': 'WEB',
        'CALLBACK_URL': 'http://127.0.0.1:8000/api/handlepayment/',
        # this is the url of handlepayment function, paytm will send a POST request to the fuction associated with this CALLBACK_URL
    }

    # everytime payment happend we will create new checksum (unique hashed string) using our merchant key
    param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, env('MERCHANTKEY'))
    # we will send the dictionary with all the credentials to the frontend
    return Response({'param_dict': param_dict})


@api_view(['POST'])
def handlepayment(request):
    checksum = ""
    # the request.POST is coming from paytm
    form = request.POST

    response_dict = {}
    order = None  # initialize the order varible with None

    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            # 'CHECKSUMHASH' is coming from paytm and we will assign it to checksum variable to verify our paymant
            checksum = form[i]

        if i == 'ORDERID':
            # we will get an order with id==ORDERID to turn isPaid=True when payment is successful
            order = Order.objects.get(id=form[i])

    # we will verify the payment using our merchant key and the checksum that we are getting from paytm request.POST
    verify = Checksum.verify_checksum(response_dict, env('MERCHANTKEY'), checksum)
    
    if verify:
        if response_dict['RESPCODE'] == '01':
            # if the response code is 01 that means our transaction is successfull
            print('order successful')
            # after successfull payment we will make isPaid=True and will save the order
            order.isPaid = True
            order.save()
            # we will render a template to display the payment status
            return render(request, 'paytm/paymentstatus.html', {'response': response_dict})
        else:
            print('order was not successful because' + response_dict['RESPMSG'])
            return render(request, 'paytm/paymentstatus.html', {'response': response_dict})
