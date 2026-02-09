import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from shop.models import Order, Payment

stripe.api_key = settings.STRIPE_SECRET_KEY

class InitiatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        provider = request.data.get("provider")

        if not order_id or not provider:
            return Response({"detail": "order_id and provider required"}, status=400)

        order = get_object_or_404(
            Order, id=order_id, user=request.user, status="pending"
        )

        payment = Payment.objects.create(
            order=order,
            user=request.user,
            provider=provider,
            amount=order.total_amount,
            status="initiated"
        )

        return Response({
            "payment_id": payment.id,
            "amount": payment.amount,
            "provider": provider
        })


class InitiateStripePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id required"}, status=400)

        order = get_object_or_404(
            Order, id=order_id, user=request.user, status="pending"
        )

        # Check if a pending payment already exists to avoid duplicate intents
        existing_payment = Payment.objects.filter(
            order=order,
            status="initiated",
            provider="stripe"
        ).order_by('-created_at').first()

        if existing_payment and existing_payment.transaction_id:
            # Retrieve the intent to ensure it is still valid
            try:
                intent = stripe.PaymentIntent.retrieve(existing_payment.transaction_id)
                if intent.status == "canceled":
                    # Mark local record as failed so we don't retrieve it again
                    existing_payment.status = "failed"
                    existing_payment.save()
                elif intent.status not in ["succeeded", "canceled"]:
                    return Response({
                        "client_secret": intent.client_secret,
                        "payment_id": existing_payment.id,
                        "stripe_public_key": settings.STRIPE_PUBLIC_KEY
                    })
            except stripe.error.StripeError:
                # If retrieval fails, proceed to create a new one
                pass

        intent = stripe.PaymentIntent.create(
            amount=int(round(order.total_amount * 100)),
            currency="usd",
            metadata={"order_id": order.id}
        )

        payment = Payment.objects.create(
            order=order,
            user=request.user,
            provider="stripe",
            transaction_id=intent.id,
            amount=order.total_amount,
            status="initiated"
        )

        return Response({
            "client_secret": intent.client_secret,
            "payment_id": payment.id,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY
        })
