#   Output some of the main fn into an alt file for simplicity
#   import packages
import json, requests, datetime
# import numpy, pandas

#   tmp var
weekday = []
weekend = []
timeframe = []
zone = []
sys_data = []

#   Create header formatting for design
print('\t<h> Order Trajectory on Timeframe </h>\n')
#   def
def daily_prep(daily):
    m = 1
    while m == 1:
        # enter code
        prod = input('What item is being updated if done press enter; ')
        stock_order = int(input('enter order amount: '))
        _ = detect_variance(stock_order)
        variance = int(input("lets do some basic calc required(to meet demand) - current(on shelf): "))
        # weekly_order(variance)
        if (prod == ''):
            m -= 1

    return
def order_biw(supplier):
    print(sys_data['property']['data']['items']['zone'][0])
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
    zone.append(zone_info)
    return zone_info
def timeframe_adj(season):
    last_proj = input('Weekday, or Weekend: ')
    # last_actual = int(input(f'What happened last {last_proj} (variance): '))
    if last_proj.lower().startswith('weekd'):
        weekday.append(last_proj)
    else:
        weekend.append(last_proj)
    if season == 'a':
        selection = 'winter'
    elif season == 'b':
        selection = 'spring'
    elif season == 'c':
        selection = 'summer'
    else:
        selection = 'fall'
    timeframe.append(selection)
    return selection
def detect_variance(stock_order):
    # tmp_stock = int(input('what is left in stock?: '))
    # surp_defic = stock_order-tmp_stock
    # print(f'order {surp_defic}')
    # proj_data=int(input('Look ahead how busy will next period be?: '))
    # calculate_order = surp_defic - proj_data
    # print(calculate_order)
# Read existing data
    try:
        with open("stock.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # Start with an empty list if file doesn't exist
    return data
# def weekly_order(variance):
#     item = input('Select an item: ')
#     while True:
#         add = int(input(f"How many of {item} per order: "))
#         break
#     return
def place_order(prod, stock_order):
    distributor = "Distributor"
    print(f"system syn: {distributor} this is the current shipment ({prod}; {stock_order})")
    shop = "Franchise"
    print(f"system ack: {shop} this is the current shipment ({prod}; {stock_order})")
    return
#   Admin tasks
def check_list(timeslip):
    emp_id = input("Enter position> ")
    if emp_id == cook:
        position_sheet = input('What is stocked?> ')
        cook = input("Are all cooked items full(y/n)?> ")
        if cook == 'y':
            print("step 1")
        elif cook == 'n':
            print("Step 2")
        else:
            print('try again')
    print(position_sheet)
    return position_sheet
#   list for day
def pull_thaw(dow, shelf):
    print("burgers\t6\tpans")
    print("bites\t4\tpans")
    print("moz\t4\tpans")
    return
#   Main
def append_to_json(new_data, filename='stock.json'):
    try:
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            if isinstance(file_data, dict) and 'items' in file_data:
                file_data['items'].append(new_data)
            else:
                raise ValueError('Expected "items" key in JSON structure.')
            file.seek(0)
            json.dump(file_data, file, indent=4)
    except FileNotFoundError:
        with open(filename,'w') as file: json.dump({'items': [new_data]}, file, indent=4)

def main():
    global sys_data
    pick_app = input('list of actions to take:\n'
                     'a\tinventory\n'
                     'b\tenter id\n'
                     'c\tother\n'
                     '(enter a,b,c)> ')
    date = datetime.date(year=2026,month=1,day=25) #    Make fn dynamic
    if pick_app == 'a':
        save_inv = input('Select an export> ')
        input_inventory = daily_prep(save_inv)
        if save_inv == 'supplier':
            print('orders on wednesday and saturday')
        elif save_inv == 'prep':
            print('cook or pan')
        elif save_inv == 'cook':
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
#   run through timeframe adj
        order = int(stock_order-variance)
        place_order(prod, stock_order)
#   Make this standard json format
        sys_data = {
            'type': 'object',
            'properties': {
                 'title': {'type': 'string', 'value': 'Order trajectory'},
                 'subtitle': {'type': 'string', 'value': 'Auto-generated order'},
                 'updated_at': {'type': 'string', 'value': str(date)},
                 'data': {
                     'type': 'array',
                     'items': [
                         {
                             'rank': {'type': 'number', 'value': 1},
                             'order_date': {'type': 'string', 'value': str(date)},
                             'current_period': {'type': 'number', 'value': season_adj},
                             'zone': {'type': 'string', 'value': zone_adj},
                             'product': {'type': 'string','value': prod},
                             'product_count': {'type': 'number', 'value': stock_order},
                             'order_calc': {'type': 'number', 'value': order}
                         }
                     ]
                 }
        }
    }
        append_to_json(sys_data)
    elif pick_app == 'b':
        dow = date
        timeslip = input("clock in> ")
        swipe_card = input('swipe card')
        shelf = check_list(timeslip)
        pull_thaw(dow, shelf)
    
    elif pick_app == 'c':
        custom = input("Manually enter intended task> ")
        print(f"starting {custom}")
    else:
        print("none")
# Read existing data
    try:
        with open("stock.json", "r") as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # Start with an empty list if file doesn't exist

# Append new data
    if pick_app == 'a':
        data.append(sys_data)

# Write updated data back
    with open("stock.json", "w") as file:
        json.dump(data, file, indent=4)
    return 
if __name__ == "__main__":
    main()
