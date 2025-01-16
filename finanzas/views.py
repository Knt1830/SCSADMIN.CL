from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def finanzas_home(request):
    context = {}
    return render(request, 'finanzas/home.html', context)