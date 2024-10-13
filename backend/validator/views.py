from django.shortcuts import render
from django.http import HttpResponse
import csv
from .validators import validate_email_address

# Function to validate a single email
def validate_email_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        result = validate_email_address(email)
        return render(request, 'result.html', {'email': email, 'result': result})
    return render(request, 'validate_email.html')

# Function to validate emails in bulk
def validate_emails_in_bulk_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        emails = []
        # Read CSV file
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        for row in reader:
            emails.append(row[0])

        results = []
        # Validate each email
        for email in emails:
            result = validate_email_address(email)
            results.append((email, result))

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="validated_emails.csv"'

        writer = csv.writer(response)
        writer.writerow(['Email', 'Validation Result'])
        writer.writerows(results)

        return response

    return render(request, 'validator/bulk_validate_email.html')
from django.conf import settings
print(settings.TEMPLATES)


