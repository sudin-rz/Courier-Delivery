from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from main.models import *

# Create your views here.


@login_required(login_url="/sign_in/?next=/courier/")
def home(request):
    return redirect(reverse('courier:available_jobs'))


@login_required(login_url="/sign_in/?next=/courier/")
def available_jobs_page(request):
    return render(request,'courier/available_jobs.html')


@login_required(login_url="/sign_in/?next=/courier/")
def available_job_page(request, id):
    job = Job.objects.filter(id=id, status=Job.PROCESSING_STATUS).last()

    if not job:
        return redirect(reverse('courier:available_jobs'))

    if request.method=='POST':
        job.courier=request.user.courier
        job.status = Job.PICKING_STATUS
        job.save()

        return redirect(reverse('courier:available_jobs'))

    return render(request,'courier/available_job.html', {
        "job": job
    })