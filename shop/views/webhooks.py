import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from shop.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception:
        return HttpResponse(status=400)

    intent = event["data"]["object"]

    if event["type"] == "payment_intent.succeeded":
        payment = Payment.objects.filter(transaction_id=intent["id"]).first()
        if payment:
            payment.status = "success"
            payment.save()
            payment.order.status = "paid"
            payment.order.save()

    elif event["type"] == "payment_intent.payment_failed":
        Payment.objects.filter(transaction_id=intent["id"]).update(status="failed")

    return HttpResponse(status=200)
