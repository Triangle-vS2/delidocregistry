'''
Docstring for inv_prod

Add an access token that represents permissions approved
Tokens are just the mechanism

This should create an app that allows a user to track inventory
categorize skus
output delivery shipment into a new json file



next steps register skus with products

route people factory - truck - warehouse - truck - customer
'''

#   Output some of the main fn into an alt file for simplicity
#   import packages
import json, datetime
import pandas as pd
#   import numpy, pandas
#   Environmental Variables
weekday = []
weekend = []
timeframe = []
zone = []
sys_data = []
skus = []
#   Create header formatting for design
print('\t<h> Inventory Products </h>\n')
#   def blocks to segment parts
def daily_prep(prod):
#   Loop through the list of products
    items = []
    skus = []
    m = 1
    while True:
        # enter code
        new_prod = input('What item is being updated if [done press enter]; ')
        if (new_prod == ''):
            break
        try:
            prod_count = int(input('Enter order amount: '))
        except ValueError:
            print('That is an invalid input!')
            continue
        items.append({'product': new_prod, 'count': prod_count})
    return items 
#   Search through json file to find associated data for departments
def order_biw(supplier):
    print(sys_data['property']['data']['items']['zone'][0])
    return
def place_order(prod, stock_order):
    destination = 'Distributor or Franchise'
    print(f"system syn: {destination} this is the current shipment ({prod}; {stock_order})")
    return
def daily_routine(truck):
    print(sys_data['property']['data']['items']['zone'][0])
    return
def morning_night(customer):
    print(sys_data['property']['data']['items']['zone'][0])
    return
#   Specify where the data should be cached
#   There needs to be an equivalent of zone that match ie. change zone to dest
#   truck, warehouse, and customer to direct prod from src -> dest

def select_zone(select_valid_zone):
    s = select_valid_zone.lower().strip()
    if s == 'a':
        zone_code = 'a'
        location = 'Dry'
    elif s == 'b':
        zone_code = 'b'
        location = 'The Walk-in'
    elif s == 'c':
        zone_code = 'c'
        location = 'Freezer'
    elif s == 'd':
        zone_code = 'd'
        location = 'Line'
    else:
        zone_code = 'e'
        location = input('Enter custom location:> ')
    zone_info = {"code": zone_code, "location": location}
#   update the json file
    zone.append(zone_info)
    return zone_info
def timeframe_adj(season):
    last_proj = input('Weekday, or Weekend: ')
    # last_actual = int(input(f'What happened last {last_proj} (variance): '))
    if last_proj.lower().startswith('weekd'):
        weekday.append(last_proj)
    else:
        weekend.append(last_proj)
#   Expected productivity; Busy, Slow, Holiday, Average
    season = season.lower()
    if season == 'a':
        selection = 'winter'
    elif season == 'b':
        selection = 'spring'
    elif season == 'c':
        selection = 'summer'
    else:
        selection = 'fall'
#   Updating Json file
    timeframe.append(selection)
    return selection
#   Admin tasks
def check_list(timeslip):
    emp_id = input("Enter position> ")
    emp_id = emp_id.lower()
    if emp_id == "cook":
        position_sheet = input('What is stocked?> ')
        cook = input("Are all cooked items full(y/n)?> ")
        if cook == 'y':
            print("step 1")
        elif cook == 'n':
            print("Step 2")
        else:
            print('try again')
#   Updating json file
    print(position_sheet)
    return position_sheet
#   list for day
def pull_thaw(dow, shelf):
    prep_sheet = {'Name': ['Burgers', 'Bites', 'Moz'], 
                  'Count': [6,4,4], 
                  'Container': ['pans', 'pans', 'pans']}
    df = pd.DataFrame(prep_sheet)
    print(df)
    return df
#   Main
### this is a reused function in multiple files ###
def append_to_json(new_data, filename='stock.json'):
    try:
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            if isinstance(file_data, dict) and 'items' in file_data:
                file_data['items'].append(new_data)
                file.seek(0)
                json.dump(file_data, file, indent=4)
                file.truncate()
            else:
                raise ValueError('Expected "items" key in JSON structure.')
    except FileNotFoundError:
        with open(filename,'w') as file: json.dump({'items': [new_data]}, file, indent=4)
def inv_prod_flow():
    global sys_data
    pick_app = input('list of actions to take:\n'
                     'a\tinventory\n'
                     'b\tenter access token\n'
                     'c\tother\n'
                     '(enter a,b,c)> ')
    date = datetime.date(year=2026,month=1,day=25) #    Make fn dynamic
    if pick_app == 'a':
        choose_export = input('Select an export> ')
        prod = daily_prep(choose_export)
        choose_export = choose_export.lower()
        if choose_export == 'supplier':
            print('orders on wednesday and saturday')
        elif choose_export == 'prep':
            print('cook or pan')
        elif choose_export == 'cook':
            print('stock or cook')
        else:
            ask_user = input('Customize as needed> ')
            print(ask_user)
        season = input('What season are we in?\n'
                        '(a)\twinter\n'
                        '(b)\tspring\n'
                        '(c)\tsummer\n'
                        '(d)\tfall\n'
                        '(enter a,b,c)> ')
        season_adj = timeframe_adj(season)
        select_valid_zone = input('Choose Zone to Access\n'
                              '(a)\tDry\n'
                              '(b)\tThe Walk-in\n'
                              '(c)\tFreezer\n'
                              '(d)\tLine\n'
                              '(e)\tCustom\n'
                              '(enter a,b,c,d,e)> ')
        zone_adj = select_zone(select_valid_zone)
#   Make this standard json format
        items_payload = []
        for i, item in enumerate(prod, start=1):
            items_payload.append(
                {
                    'rank': i,
                    'order_date': str(date),
                    'current_period': season_adj,
                    'zone': zone_adj,
                    'product': item['product'],
                    'product_count': item['count'],
                    'order_calc': item['count'],
                }
            )
        sys_data = {
            'type': 'object',
            'properties': {
                 'title': 'Order trajectory',
                 'subtitle': 'Auto-generated order',
                 'updated_at': str(date),
                 'data': {
                     'type': 'array',
                     'items': items_payload,
                 },
        },
    }
        append_to_json(sys_data)
    elif pick_app == 'b':
        dow = date
        timeslip = int(input("clock in> "))
        if timeslip >= 1:
            print('Access level high')
        elif timeslip >= -1:
            print('Access level basic')
        elif timeslip < -1:
            print('Access Denied')
        else:
            print('A friendly reminder your lack common sense (pebkau error)')
        swipe_card = input('present card for multi-factor auth')
        shelf = check_list(timeslip)
        pull_thaw(dow, shelf)
    elif pick_app == 'c':
        custom = input("Manually enter intended task> ")
        print(f"starting {custom}")
    else:
        print("none")
    return 
if __name__ == "__main__":
    inv_prod_flow()
