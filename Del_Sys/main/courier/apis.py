from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from main.models import *
from django.conf import settings

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

