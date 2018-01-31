from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from core.models import Organisation, Contact, Sector, Currency, Spreadsheet, Entry
from unicodecsv import writer as csvwriter
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from django.http import *
from django.contrib.auth.decorators import login_required
from .forms import SpreadsheetForm
from .util import *
from django.db.models import Sum
from itertools import chain, groupby
from django.db.models import Case, When, Value, IntegerField

@login_required
def edit(request,year):
    warnings = []
    sector_range = ["new_sector{}".format(i) for i in range(1,7)]
    user = request.user
    contact = get_object_or_404(Contact,user=user)
    organisation = contact.organisation
    recipients = Entry.RECIPIENT_CHOICES
    statuses = Entry.PLEDGE_OR_DISB_CHOICES
    #Needed to order "Other"
    annotated_sectors = Sector.objects.annotate(
        other=Case(
            When(name="Other (please detail in comments box)",then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )
    if not organisation.sectors.all():
        if not organisation.disable_default_loan_sectors:
            sectors = annotated_sectors.filter(default=True).order_by("other","name")
        else:
            sectors = annotated_sectors.filter(default=True,loan_or_grant="G").order_by("other","name")
    else:
        organisationSectors = organisation.sectors.annotate(
            other=Case(
                When(name="Other (please detail in comments box)",then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).all()
        if not organisation.disable_default_loan_sectors:
            defaultSectors = annotated_sectors.filter(default=True)
        else:
            defaultSectors = annotated_sectors.filter(default=True,loan_or_grant="G")
        unionSectors = organisationSectors | defaultSectors
        sectors = unionSectors.distinct().order_by("other","name")
    channels = Entry.DELIVERY_CHOICES
    facilities = Entry.FACILITY_CHOICES
    appeal_statuses = Entry.APPEAL_STATUS_CHOICES
    years = Spreadsheet.YEAR_CHOICES
    filtered_years = years[-3:]
    year = int(year)
    year_verbose = dict(years)[year]
    if request.method == "POST":
        form = SpreadsheetForm(request.POST)
        queryDict = request.POST
        comment = queryDict.get('comment')
        if not Spreadsheet.objects.filter(organisation=organisation,year=year).exists():
            spreadsheet = form.save(commit=False)
            spreadsheet.year = year
            spreadsheet.organisation = organisation
            spreadsheet.save()
        else:
            spreadsheet = Spreadsheet.objects.get(organisation=organisation,year=year)
            form = SpreadsheetForm(request.POST,instance=spreadsheet)
            spreadsheet = form.save()
        #Look for new sectors
        new_sector_dict = {}
        for key, value in queryDict.iteritems():
            if key in sector_range:
                if value!="":
                    new_sector_dict[key] = value
                    new_sector = Sector(name=value,loan_or_grant="L")
                    new_sector.save()
                    organisation.sectors.add(new_sector)
        excludeKeys = ["currency","comment","multiyear_comment","total_grants","remaining_grants","csrfmiddlewaretoken"]+sector_range
        for key, value in queryDict.iteritems():
            if Entry.objects.filter(spreadsheet=spreadsheet,coordinates=key).exists():
                entry = Entry.objects.get(spreadsheet=spreadsheet,coordinates=key)
                if safeFloat(value)>=0:
                    entry.amount = safeFloat(value)
                    entry.save_reverse()
                else:
                    entry.delete()
            elif key not in excludeKeys and value!="":
                entry = Entry()
                entry.spreadsheet = spreadsheet
                split_coords = key.split("|")
                entry_sector = split_coords[4]
                if entry_sector in sector_range:
                    new_sector = new_sector_dict[entry_sector]
                    split_coords[4] = new_sector
                    key = "|".join(split_coords)
                entry.coordinates = key
                if safeFloat(value)>=0:
                    entry.amount = safeFloat(value)
                    entry.save_reverse()
        return redirect(spreadsheet)
    else:
        if Spreadsheet.objects.filter(organisation=organisation,year=year).exists():
            spreadsheet = Spreadsheet.objects.get(organisation=organisation,year=year)
            form = SpreadsheetForm(instance=spreadsheet)
            entries = Entry.objects.filter(spreadsheet=spreadsheet)
            currency = spreadsheet.currency
            spreadsheet_exists = True
            #Validate sums here
            #Grants table
            gt = entries.filter(spreadsheet=spreadsheet,loan_or_grant="G",concessional=True,appeal=False,facility="",channel_of_delivery="",sector__isnull=True).exclude(pledge_or_disbursement="P")
            gt_sum = gt.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            gt_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in gt_sum}
            #Sector grants
            sg = entries.filter(spreadsheet=spreadsheet,loan_or_grant="G",concessional=True,appeal=False,facility="",channel_of_delivery="",sector__isnull=False)
            sg_sum = sg.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            sg_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in sg_sum} 
            #Channel grants
            cg = entries.filter(spreadsheet=spreadsheet,loan_or_grant="G",concessional=True,appeal=False,facility="",sector__isnull=True)
            cg_sum = cg.values('recipient').annotate(total = Sum('amount')).order_by('recipient').exclude(channel_of_delivery="")
            cg_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in cg_sum}
            #Compare grants
            for recipient,recipient_name in recipients:
                if recipient not in ["M","R"]:
                    total_grants = 0
                    if recipient in gt_sum_obj:
                        total_grants = total_grants + gt_sum_obj[recipient]
                    if recipient in sg_sum_obj:
                        grant_sectors = sg_sum_obj[recipient]
                        if total_grants>grant_sectors:
                            warnings.append("Warning: Total grants do not equal grants by sector for %s. Total grants are greater by %s" % (recipient_name,(total_grants-grant_sectors)))
                        if total_grants<grant_sectors:
                            warnings.append("Warning: Total grants do not equal grants by sector for %s. Grants by sector are greater by %s" % (recipient_name,(grant_sectors-total_grants)))
                    if recipient in cg_sum_obj:
                        grant_channels = cg_sum_obj[recipient]
                        if total_grants>grant_channels:
                            warnings.append("Warning: Total grants do not equal grants by channel of delivery for %s. Total grants are greater by %s" % (recipient_name,(total_grants-grant_channels)))
                        if total_grants<grant_channels:
                            warnings.append("Warning: Total grants do not equal grants by channel of delivery for %s. Grants by channel of delivery are greater by %s" % (recipient_name,(grant_channels-total_grants)))
            #Loans table (both concessional and non-concessional)
            lt = entries.filter(spreadsheet=spreadsheet,loan_or_grant="L",sector__isnull=True,channel_of_delivery="").exclude(pledge_or_disbursement="P")
            lt_sum = lt.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            lt_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in lt_sum} 
            #Sector loans
            sl = entries.filter(spreadsheet=spreadsheet,loan_or_grant="L",sector__isnull=False)
            sl_sum = sl.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            sl_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in sl_sum}
            #Channel loans
            cl = entries.filter(spreadsheet=spreadsheet,loan_or_grant="L")
            cl_sum = cl.values('recipient').annotate(total = Sum('amount')).order_by('recipient').exclude(channel_of_delivery="")
            cl_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in cl_sum} 
            #Compare loans
            for recipient,recipient_name in recipients:
                total_loans = 0
                if recipient in lt_sum_obj:
                    total_loans = total_loans + lt_sum_obj[recipient]
                if recipient in sl_sum_obj:
                    loan_sectors = sl_sum_obj[recipient]
                    if total_loans>loan_sectors:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by sector for %s. Total loans are greater by %s" % (recipient_name,(total_loans-loan_sectors)))
                    if total_loans<loan_sectors:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by sector for %s. Loans by sector are greater by %s" % (recipient_name,(loan_sectors-total_loans)))
                if recipient in cl_sum_obj:
                    loan_channels = cl_sum_obj[recipient]
                    if total_loans>loan_channels:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by channel for %s. Total loans are greater by %s" % (recipient_name,(total_loans-loan_channels)))
                    if total_loans<loan_channels:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by channel for %s. Loans by channel are greater by %s" % (recipient_name,(loan_channels-total_loans)))
                
        else:
            form = SpreadsheetForm()
            entries = []
            currency = []
            spreadsheet_exists = False
    return render(request,'core/edit-locked.html', {"warnings":warnings,"user":user,"contact":contact,"form":form,"entries":entries,"recipients":recipients,"statuses":statuses,"facilities":facilities,"appeal_statuses":appeal_statuses,"sectors":sectors,"channels":channels,"years":filtered_years,"selected_year":year,"year_verbose":year_verbose,"currency":currency,"sector_range":sector_range,"spreadsheet_exists":spreadsheet_exists})

@login_required
def adminEdit(request,slug,year):
    warnings = []
    sector_range = ["new_sector{}".format(i) for i in range(1,7)]
    user = request.user
    if not user.is_staff:
        return redirect("core.views.edit",year=year)
    contact = get_object_or_404(Contact,user=user)
    organisation = Organisation.objects.get(slug=slug)
    recipients = Entry.RECIPIENT_CHOICES
    statuses = Entry.PLEDGE_OR_DISB_CHOICES
    #Needed to order "Other"
    annotated_sectors = Sector.objects.annotate(
        other=Case(
            When(name="Other (please detail in comments box)",then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    )
    if not organisation.sectors.all():
        if not organisation.disable_default_loan_sectors:
            sectors = annotated_sectors.filter(default=True).order_by("other","name")
        else:
            sectors = annotated_sectors.filter(default=True,loan_or_grant="G").order_by("other","name")
    else:
        organisationSectors = organisation.sectors.annotate(
            other=Case(
                When(name="Other (please detail in comments box)",then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).all()
        if not organisation.disable_default_loan_sectors:
            defaultSectors = annotated_sectors.filter(default=True)
        else:
            defaultSectors = annotated_sectors.filter(default=True,loan_or_grant="G")
        unionSectors = organisationSectors | defaultSectors
        sectors = unionSectors.distinct().order_by("other","name")
    channels = Entry.DELIVERY_CHOICES
    facilities = Entry.FACILITY_CHOICES
    appeal_statuses = Entry.APPEAL_STATUS_CHOICES
    years = Spreadsheet.YEAR_CHOICES
    year = int(year)
    year_verbose = dict(years)[year]
    if request.method == "POST":
        form = SpreadsheetForm(request.POST)
        queryDict = request.POST
        comment = queryDict.get('comment')
        if not Spreadsheet.objects.filter(organisation=organisation,year=year).exists():
            spreadsheet = form.save(commit=False)
            spreadsheet.year = year
            spreadsheet.organisation = organisation
            spreadsheet.save()
        else:
            spreadsheet = Spreadsheet.objects.get(organisation=organisation,year=year)
            form = SpreadsheetForm(request.POST,instance=spreadsheet)
            spreadsheet = form.save()
        #Look for new sectors
        new_sector_dict = {}
        for key, value in queryDict.iteritems():
            if key in sector_range:
                if value!="":
                    new_sector_dict[key] = value
                    new_sector = Sector(name=value,loan_or_grant="G")
                    new_sector.save()
                    organisation.sectors.add(new_sector)
        excludeKeys = ["currency","comment","multiyear_comment","total_grants","remaining_grants","csrfmiddlewaretoken"]+sector_range
        for key, value in queryDict.iteritems():
            if Entry.objects.filter(spreadsheet=spreadsheet,coordinates=key).exists():
                entry = Entry.objects.get(spreadsheet=spreadsheet,coordinates=key)
                if safeFloat(value)>=0:
                    entry.amount = safeFloat(value)
                    entry.save_reverse()
                else:
                    entry.delete()
            elif key not in excludeKeys and value!="":
                entry = Entry()
                entry.spreadsheet = spreadsheet
                split_coords = key.split("|")
                entry_sector = split_coords[4]
                if entry_sector in sector_range:
                    new_sector = new_sector_dict[entry_sector]
                    split_coords[4] = new_sector
                    key = "|".join(split_coords)
                entry.coordinates = key
                if safeFloat(value)>=0:
                    entry.amount = safeFloat(value)
                    entry.save_reverse()
        return redirect("core.views.adminEdit",slug=slug,year=year)
    else:
        if Spreadsheet.objects.filter(organisation=organisation,year=year).exists():
            spreadsheet = Spreadsheet.objects.get(organisation=organisation,year=year)
            form = SpreadsheetForm(instance=spreadsheet)
            entries = Entry.objects.filter(spreadsheet=spreadsheet)
            currency = spreadsheet.currency
            spreadsheet_exists = True
            #Validate sums here
            #Grants table
            gt = entries.filter(spreadsheet=spreadsheet,loan_or_grant="G",concessional=True,facility="",channel_of_delivery="",sector__isnull=True).exclude(pledge_or_disbursement="P")
            gt_sum = gt.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            gt_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in gt_sum} 
            #Sector grants
            sg = entries.filter(spreadsheet=spreadsheet,loan_or_grant="G",concessional=True,facility="",channel_of_delivery="",sector__isnull=False)
            sg_sum = sg.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            sg_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in sg_sum} 
            #Channel grants
            cg = entries.filter(spreadsheet=spreadsheet,loan_or_grant="G",concessional=True,facility="",sector__isnull=True)
            cg_sum = cg.values('recipient').annotate(total = Sum('amount')).order_by('recipient').exclude(channel_of_delivery="")
            cg_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in cg_sum}
            #Compare grants
            for recipient,recipient_name in recipients:
                if recipient not in ["M","R"]:
                    total_grants = 0
                    if recipient in gt_sum_obj:
                        total_grants = total_grants + gt_sum_obj[recipient]
                    if recipient in sg_sum_obj:
                        grant_sectors = sg_sum_obj[recipient]
                        if total_grants>grant_sectors:
                            warnings.append("Warning: Total grants do not equal grants by sector for %s. Total grants are greater by %s" % (recipient_name,(total_grants-grant_sectors)))
                        if total_grants<grant_sectors:
                            warnings.append("Warning: Total grants do not equal grants by sector for %s. Grants by sector are greater by %s" % (recipient_name,(grant_sectors-total_grants)))
                    if recipient in cg_sum_obj:
                        grant_channels = cg_sum_obj[recipient]
                        if total_grants>grant_channels:
                            warnings.append("Warning: Total grants do not equal grants by channel of delivery for %s. Total grants are greater by %s" % (recipient_name,(total_grants-grant_channels)))
                        if total_grants<grant_channels:
                            warnings.append("Warning: Total grants do not equal grants by channel of delivery for %s. Grants by channel of delivery are greater by %s" % (recipient_name,(grant_channels-total_grants)))
            #Loans table (both concessional and non-concessional)
            lt = entries.filter(spreadsheet=spreadsheet,loan_or_grant="L",sector__isnull=True,channel_of_delivery="").exclude(pledge_or_disbursement="P")
            lt_sum = lt.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            lt_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in lt_sum} 
            #Sector loans
            sl = entries.filter(spreadsheet=spreadsheet,loan_or_grant="L",sector__isnull=False)
            sl_sum = sl.values('recipient').annotate(total = Sum('amount')).order_by('recipient')
            sl_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in sl_sum}
            #Channel loans
            cl = entries.filter(spreadsheet=spreadsheet,loan_or_grant="L")
            cl_sum = cl.values('recipient').annotate(total = Sum('amount')).order_by('recipient').exclude(channel_of_delivery="")
            cl_sum_obj = {this_sum['recipient']:this_sum['total'] for this_sum in cl_sum} 
            #Compare loans
            for recipient,recipient_name in recipients:
                total_loans = 0
                if recipient in lt_sum_obj:
                    total_loans = total_loans + lt_sum_obj[recipient]
                if recipient in sl_sum_obj:
                    loan_sectors = sl_sum_obj[recipient]
                    if total_loans>loan_sectors:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by sector for %s. Total loans are greater by %s" % (recipient_name,(total_loans-loan_sectors)))
                    if total_loans<loan_sectors:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by sector for %s. Loans by sector are greater by %s" % (recipient_name,(loan_sectors-total_loans)))
                if recipient in cl_sum_obj:
                    loan_channels = cl_sum_obj[recipient]
                    if total_loans>loan_channels:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by channel for %s. Total loans are greater by %s" % (recipient_name,(total_loans-loan_channels)))
                    if total_loans<loan_channels:
                        warnings.append("Warning: Total loans (concessional and non-concessional) do not equal loans by channel for %s. Loans by channel are greater by %s" % (recipient_name,(loan_channels-total_loans)))
                
        else:
            form = SpreadsheetForm()
            entries = []
            currency = []
            spreadsheet_exists = False
    return render(request,'core/edit.html', {"warnings":warnings,"user":user,"contact":contact,"organisation":organisation,"form":form,"entries":entries,"recipients":recipients,"statuses":statuses,"facilities":facilities,"appeal_statuses":appeal_statuses,"sectors":sectors,"channels":channels,"years":years,"selected_year":year,"year_verbose":year_verbose,"currency":currency,"sector_range":sector_range,"spreadsheet_exists":spreadsheet_exists})

@login_required
def index(request):
    user = request.user
    return render_to_response('core/home.html', {"user":user})

@login_required
def csv(request,slug):
    organisation = get_object_or_404(Organisation,slug=slug)
    spreadsheets = Spreadsheet.objects.filter(organisation=organisation)
    entries = Entry.objects.filter(spreadsheet__in=spreadsheets)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="'+slug+'.csv"'
    writer = csvwriter(response,encoding='utf-8')
    header = ["Organisation","Loan or grant","Concessional","Status"
              ,"Recipient","Sector","Channel of delivery","Year","Amount","Currency"
              ,"Facility"
              ,"Comment"]
    writer.writerow(header)
    for entry in entries:
        year = entry.spreadsheet.year_translate()
        #Edit here for future years
        if year in [2017,2018,"2019-2020"]:
            comment = entry.spreadsheet.comment
            currency = entry.spreadsheet.currency
            writer.writerow([organisation
                             ,entry.loan_or_grant_translate()
                             ,entry.concessional_translate()
                             ,entry.pledge_or_disbursement_translate()
                             ,entry.recipient_translate()
                             ,entry.sector
                             ,entry.channel_of_delivery_translate()
                             ,year
                             ,entry.amount
                             ,currency
                             ,entry.facility_translate()
                             ,comment
                             ])
    return response

@login_required
def csv_all(request):
    user = request.user
    if user.is_staff:
        entries = Entry.objects.all()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all.csv"'
        writer = csvwriter(response,encoding='utf-8')
        header = ["Organisation","Loan or grant","Concessional","Appeal","Appeal status","Status"
                  ,"Recipient","Sector","Channel of delivery","Year","Amount","Currency"
                  ,"Facility","Comment"]
        writer.writerow(header)
        for entry in entries:
            organisation = entry.spreadsheet.organisation
            year = entry.spreadsheet.year_translate()
            comment = entry.spreadsheet.comment
            currency = entry.spreadsheet.currency
            writer.writerow([organisation
                             ,entry.loan_or_grant_translate()
                             ,entry.concessional_translate()
                             ,entry.appeal_translate()
                             ,entry.appeal_status_translate()
                             ,entry.pledge_or_disbursement_translate()
                             ,entry.recipient_translate()
                             ,entry.sector
                             ,entry.channel_of_delivery_translate()
                             ,year
                             ,entry.amount
                             ,currency
                             ,entry.facility_translate()
                             ,comment
                             ])
        return response
    else:
        return redirect(user.contact.organisation)

def login_user(request):
    logout(request)
    nextURL = request.GET.get('next')
    print(nextURL)
    username = password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        nextURL = request.POST.get('next')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                if nextURL is not None:
                  return HttpResponseRedirect(nextURL)
                else:
                  return HttpResponseRedirect('/')
    return render(request,'core/login.html', {'next':nextURL})