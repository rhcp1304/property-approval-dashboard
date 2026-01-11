from django.shortcuts import render, get_object_or_404, redirect
from .models import PropertyRecord

def dashboard(request):
    # Sort Pending items to the top for the leader to review
    props = PropertyRecord.objects.all().order_by('status', '-year', '-weekly_date')
    return render(request, 'property/dashboard.html', {'properties': props})

def veto_action(request, pk):
    if request.method == "POST":
        prop = get_object_or_404(PropertyRecord, pk=pk)
        decision = request.POST.get('decision')
        if decision in [PropertyRecord.VetoDecision.APPROVE, PropertyRecord.VetoDecision.DROP]:
            prop.status = decision
            prop.save()
    return redirect('dashboard')