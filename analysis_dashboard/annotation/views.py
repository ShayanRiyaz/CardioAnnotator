from django.shortcuts import render

def annotation(request):
    return render(request, 'annotation/annotation.html')