from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q
from .models import Complaint, ComplaintCategory, ComplaintStatus
from .forms import ComplaintForm, StatusUpdateForm


def complaint_list_view(request):
    query = request.GET.get('q')
    complaints = Complaint.objects.all()

    if query:
        complaints = complaints.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(status__icontains=query)
        )

    context = {
        'complaints': complaints,
        'query': query,
    }
    return render(request, 'complaints/list.html', context)


def create_complaint_view(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('complaint_list')
    else:
        form = ComplaintForm()

    return render(request, 'complaints/create.html', {'form': form})


def complaint_detail_view(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    return render(request, 'complaints/detail.html', {'complaint': complaint})


def update_complaint_status_view(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == 'POST':
        form = StatusUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = StatusUpdateForm(instance=complaint)

    return render(request, 'complaints/update_status.html', {
        'form': form,
        'complaint': complaint,
    })
