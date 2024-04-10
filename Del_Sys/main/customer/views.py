from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from main.customer import forms

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

import firebase_admin
from firebase_admin import credentials,auth

import stripe

from django.conf import settings

from main.models import Job,Transaction

import requests
from django.http import JsonResponse

import googlemaps
from datetime import datetime

from .graph import calculate_distance

cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIAL)
firebase_admin.initialize_app(cred)

stripe.api_key= settings.STRIPE_API_SECRET_KEY

@login_required()
def home(request):
    return redirect(reverse('customer:profile'))

@login_required(login_url="/sign_in/?next=/customer")
def profile_page(request):
    user_form = forms.BasicUserForm(instance=request.user)
    customer_form = forms.BasicCustomerForm(instance=request.user.customer)
    password_form= PasswordChangeForm(request.user)

    if request.method == "POST":

        if request.POST.get('action')=='update_profile':
            user_form = forms.BasicUserForm(request.POST, instance=request.user)
            customer_form = forms.BasicCustomerForm(request.POST, request.FILES, instance=request.user.customer)

            if user_form.is_valid() and customer_form.is_valid():
                user_form.save()
                customer_form.save()

                if not messages.get_messages(request):
                    messages.success(request, 'Your Profile has been updated')
                return redirect(reverse('customer:profile'))

        elif request.POST.get('action')=='update_password':
            password_form= PasswordChangeForm(request.user,request.POST)
            if password_form.is_valid():
                user=password_form.save()
                update_session_auth_hash(request,user)

                messages.success(request, 'Your Password has been updated')
                return redirect(reverse('customer:profile'))
        
        elif request.POST.get('action')=='update_phone':
            #Get Firebase user data
            firebase_user=auth.verify_id_token(request.POST.get('id_token'))

            request.user.customer.phone_number=firebase_user['phone_number']
            request.user.customer.save()
            return redirect(reverse('customer:profile'))


    return render(request, 'customer/profile.html', {
        "user_form": user_form,
        "customer_form": customer_form,
        "password_form": password_form,
    })



@login_required(login_url="/sign_in/?next=/customer")
def payment_method_page(request):
    current_customer=request.user.customer

    # # Remove Existing Card
    if request.method=="POST":
        stripe.PaymentMethod.detach(current_customer.stripe_payment_method_id)
        current_customer.stripe_payment_method_id=""
        current_customer.stripe_card_last4=""
        current_customer.save()
        return redirect(reverse('customer:payment_method'))



    #save stripe customer info
    if not current_customer.stripe_customer_id:
        customer=stripe.Customer.create()
        current_customer.stripe_customer_id=customer['id']
        current_customer.save()
# --------------------------------here to ------------------
    #Get stripe payment method
    stripe_payment_methods=stripe.PaymentMethod.list(
        customer=current_customer.stripe_customer_id,
        type="card",
    )

    print(stripe_payment_methods)

    if stripe_payment_methods and len(stripe_payment_methods.data) > 0:
        payment_method=stripe_payment_methods.data[0]
        current_customer.stripe_payment_method_id=payment_method.id
        current_customer.stripe_card_last4=payment_method.card.last4
        current_customer.save()
    
    else:
        current_customer.stripe_payment_method_id=""
        current_customer.stripe_card_last4= ""
        current_customer.save()    

# if not current_customer.stripe_customer_id:

    intent=stripe.SetupIntent.create(
                    customer=current_customer.stripe_customer_id
                )

    return render(request,'customer/payment_method.html',{
                    "client_secret": intent.client_secret,
                    "STRIPE_API_PUBLIC_KEY": settings.STRIPE_API_PUBLIC_KEY,
                })

#  ---------------remove this 
    # return render(request,'customer/payment_method.html')


@login_required(login_url="/sign_in/?next=/customer")
def create_job_page(request):
    current_customer = request.user.customer 

    if not request.user.customer.stripe_customer_id:
        return redirect(reverse('customer:payment_method'))

    has_current_job = Job.objects.filter(
        customer= current_customer,
        status__in=[
            Job.PROCESSING_STATUS,
            Job.PICKING_STATUS,
            Job.DELIVERING_STATUS
        ]
    ).exists()

    if has_current_job:
        messages.warning(request, "You currently have a processing job.")
        return redirect(reverse('customer:current_jobs'))

    creating_job = Job.objects.filter(customer=current_customer, status=Job.CREATING_STATUS).last()
    step1_form = forms.JobCreateStep1Form(instance=creating_job)
    step2_form = forms.JobCreateStep2Form(instance=creating_job)
    step3_form = forms.JobCreateStep3Form(instance=creating_job)
    

    if request.method == "POST":
        if request.POST.get('step') == '1':  # Corrected the condition here
            step1_form = forms.JobCreateStep1Form(request.POST, request.FILES, instance=creating_job)
            if step1_form.is_valid():
                creating_job = step1_form.save(commit=False)
                creating_job.customer = current_customer
                creating_job.save()
                print("Name:", creating_job.name)
                print("Description:", creating_job.description)
                return redirect(reverse('customer:create_job'))

        
        elif request.POST.get('step')=='2':
            step2_form= forms.JobCreateStep2Form(request.POST, instance=creating_job)
            if step2_form.is_valid():
                creating_job=step2_form.save()           
                return redirect(reverse('customer:create_job'))


        elif request.POST.get('step')=='3':
            step3_form= forms.JobCreateStep3Form(request.POST, instance=creating_job)
            if step3_form.is_valid():
                creating_job=step3_form.save()
            if creating_job.pickup_lat and creating_job.pickup_lng and creating_job.delivery_lat and creating_job.delivery_lng:
                distance, duration, price = calculate_distance(creating_job.pickup_lat, creating_job.pickup_lng, creating_job.delivery_lat, creating_job.delivery_lng)
                creating_job.distance = round(distance,2)
                creating_job.duration = duration
                creating_job.price = round(price,2)
                creating_job.save()
                return redirect(reverse('customer:create_job'))


        

        elif request.POST.get('step') == '4':
            if creating_job.price:
                try:
                    payment_intent = stripe.PaymentIntent.create(
                        amount=int(creating_job.price),
                        currency='inr',
                        customer=current_customer.stripe_customer_id,
                        payment_method=current_customer.stripe_payment_method_id,
                        off_session=True,
                        confirm=True,
                    )

                    print("Payment Intent ID:", payment_intent.id)  # Debug print for payment intent ID

                    # Create Transaction and update status
                    Transaction.objects.create(
                        stripe_payment_intent_id=payment_intent.id,  # Use payment_intent.id instead of ['id']
                        job=creating_job,
                        amount=creating_job.price
                    )

                    creating_job.status = Job.PROCESSING_STATUS  # Update the status
                    creating_job.save() # Save the creating_job object after setting the status
                    
                    messages.success(request, 'Order created successfully') 

                    return redirect(reverse('customer:home'))

                    print("Job Status:", creating_job.status)  # Debug print for job status

                except stripe.error.CardError as e:
                    err = e.error
                    # Error code will be authentication_required if authentication is needed
                    print("Code is: %s" % err.code)
                    payment_intent_id = err.payment_intent['id']
                    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            # Ensure the current status is correct
        print("Current Job Status:", creating_job.status)  # Debug print for current job status


        
    #Determine the current step
    if not creating_job:
        current_step=1
    elif creating_job.delivery_name:
        current_step=4        
    elif creating_job.pickup_name:
        current_step=3
    else:
        current_step=2


    
    return render(request, 'customer/create_job.html', {
        "step1_form": step1_form,
        "step2_form": step2_form,
        "step3_form": step3_form,
        "job": creating_job,
        "step":current_step,
    })


@login_required(login_url="/sign_in/?next=/customer")
def current_jobs_page(request):
    jobs= Job.objects.filter(
        customer= request.user.customer,
        status__in=[
            Job.PROCESSING_STATUS,
            Job.PICKING_STATUS,
            Job.DELIVERING_STATUS
        ]
    )

    return render(request, 'customer/jobs.html',{
        "jobs":jobs
    })


@login_required(login_url="/sign_in/?next=/customer")
def archived_jobs_page(request):
    jobs= Job.objects.filter(
        customer= request.user.customer,
        status__in=[
            Job.COMPLETED_STATUS,
            Job.CANCELED_STATUS,
        ]
    )

    return render(request, 'customer/jobs.html',{
        "jobs":jobs
    })


@login_required(login_url="/sign_in/?next=/customer")
def job_page(request,job_id):
    job= Job.objects.get(id=job_id)

    if request.method=="POST" and job.status==Job.PROCESSING_STATUS:
        job.status= Job.CANCELED_STATUS
        job.save()
        return redirect(reverse('customer:archived_jobs'))

    return render(request, 'customer/job.html',{
        "job": job
    })