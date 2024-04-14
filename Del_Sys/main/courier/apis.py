from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from main.models import *
from django.conf import settings
from django.utils import timezone

@csrf_exempt
@login_required(login_url="/courier/sign_in/")
def available_jobs_api(request):
    jobs = list(Job.objects.filter(status=Job.PROCESSING_STATUS).values())

    for job in jobs:
        job['photo'] = settings.MEDIA_URL + job['photo']


    return JsonResponse({
        "success": True,
        "jobs": jobs
    })



@csrf_exempt
@login_required(login_url="/courier/sign_in/")
def current_job_update_api(request, id):
    job= Job.objects.filter(
        id=id,
        courier=request.user.courier,
        status__in=[
            Job.PICKING_STATUS,
            Job.DELIVERING_STATUS
        ]
    ).last()

    if job.status==Job.PICKING_STATUS:
        job.pickup_photo = request.FILES['pickup_photo']
        job.pickedup_at = timezone.now()
        job.status=Job.DELIVERING_STATUS
        job.save()

    elif job.status==Job.DELIVERING_STATUS:
        job.delivery_photo = request.FILES['delivery_photo']
        job.delivered_at = timezone.now()
        job.status=Job.COMPLETED_STATUS
        job.save()

    return JsonResponse({
        "success": True
    })