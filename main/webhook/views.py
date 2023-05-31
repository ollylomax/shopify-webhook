import os
import json
from pyairtable import Table
from pyairtable.formulas import match
from django.shortcuts import render

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# Create empty batch list
batch = []

# Decorators
@require_POST
@csrf_exempt
def webhook(request):

    # Decode json payload
    body = request.body.decode("utf-8")
    # Load into python
    data = json.loads(body)

    # Inventory Item ID of updated Variant from webhook
    updated_item = data['inventory_item_id']
    # Updated Quantity of Variant from webhook
    updated_quantity = data['available']

    # Airtable API
    api_key = ''
    # Instantiate table with creds
    table = Table(api_key, '', '')
    # Find Airtable record matching the Inventory ID from webhook
    item_record = table.all(formula=match({"Inventory Item ID": updated_item}))

    # Search for duplicate items in batch list
    if any(item['id'] == item_record[0]['id'] for item in batch):
        # If duplicate found, iterate over batch list and update with quantity from webhook
        for item in batch:
            if item['id'] == item_record[0]['id']:
                item.update({"id": item_record[0]['id'], "fields": {"Quantity": updated_quantity}})
                print(f'Quantity of {item_record[0]["id"]} updated in batch file')
    # Insert item dict into batch list
    else:
        batch.append({"id": item_record[0]['id'], "fields": {"Quantity": updated_quantity}})
        print(f'Quantity of {item_record[0]["id"]} stored in batch file')
    
    if len(batch) >= 10:
        payload = batch
        print('Batch updating Airtable with payload...')
        table.batch_update(payload)
        print('Payload delivered, wiping batch data...')
        batch.clear()
        print('Success')
    else:
        payload = []

    return render(request, 'webhook/webhook.html')
