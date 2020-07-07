import csv
import re 
import nltk
import requests

from dateutil.parser import parse
from nltk.tokenize import word_tokenize

'''
    get death count by congressional district
    start with all deaths, then once the algorithm is done break down to time frames
'''

'''
    CSSEGIC-COVID-19 folder = covid-19 death data over time by county
    deaths_by_district = results folder, currently csv for each state
    states_and_distrcts = county to district population and afact data
'''
state_abbrev = {"Alabama" : "AL","Alaska" : "AK","Arizona" : "AZ","Arkansas" : "AR","California" : "CA","Colorado" : "CO","Connecticut" : "CT","Delaware" : "DE","Florida" : "FL","Georgia" : "GA","Hawaii" : "HI","Idaho" : "ID","Illinois" : "IL","Indiana" : "IN","Iowa" : "IA","Kansas" : "KS","Kentucky" : "KY","Louisiana" : "LA","Maine" : "ME","Maryland" : "MD","Massachusetts" : "MA","Michigan" : "MI","Minnesota" : "MN","Mississippi" : "MS","Missouri" : "MO","Montana" : "MT","Nebraska" : "NE","Nevada" : "NV","New Hampshire" : "NH","New Jersey" : "NJ","New Mexico" : "NM","New York" : "NY","North Carolina" : "NC","North Dakota" : "ND","Ohio" : "OH","Oklahoma" : "OK","Oregon" : "OR","Pennsylvania" : "PA","Rhode Island" : "RI","South Carolina" : "SC","South Dakota" : "SD","Tennessee" : "TN","Texas" : "TX","Utah" : "UT","Vermont" : "VT","Virginia" : "VA","Washington" : "WA","West Virginia" : "WV","Wisconsin" : "WI","Wyoming" : "WY"}
not_counties = {}

# returns True if date is valid calendar date, ex: 6/45/20 -> False, 4/12/20 -> True
#   and if the date falls in the range 1/22/20 - whatever the most updated date in time_......csv
def valid_date(date):
    # reader for the csv file
    deaths_by_county = open('CSSEGIS-COVID-19/time_series_covid19_deaths_US.csv','r')
    deaths_by_county_reader = csv.reader(deaths_by_county)
    # column headers    
    row = next(deaths_by_county_reader)

    recent = row[len(row)-1]
    recent_date = [int(r) for r in recent.split("/")]

    try:
        parse(date)
    except ValueError:
        return False
    date_split = [int(d) for d in date.split("/")]
    if(date_split[0] > recent_date[0] or date_split[0] < 1 or (date_split[0] == recent_date[0] and date_split[1] > recent_date[1]) or (date_split[0] == 1 and date_split[1] < 22) or date_split[2] != 20):
        print("invalid date: ",date)
        return False
    return True

# returns list of dates between start_date and end_date as strings in MM/DD/YY form
def dates_between(start_date,end_date):
    if(not valid_date(start_date) or not valid_date(end_date)):
        return []
    
    dates = []
    # get time.....csv and find column headers that match start and end, avoids converting from string to date to string again
    deaths_by_county = open('CSSEGIS-COVID-19/time_series_covid19_deaths_US.csv','r')
    deaths_by_county_reader = csv.reader(deaths_by_county)
    # column headers    
    row = next(deaths_by_county_reader)
    deaths_by_county.close()

    start_index = 0
    end_index = 0

    start_date_split = [int(s) for s in start_date.split("/")]
    end_date_split = [int(e) for e in end_date.split("/")]

    for x in range(12,len(row)):
        date = [int(d) for d in row[x].split("/")]
        if(date == start_date_split):
            start_index = x
        elif(date == end_date_split):
            end_index = x

        if(start_index > 0 and end_index > 0):
            if(start_index > end_index):
                print("end date is chronologically before start date",start_date,end_date)
                return None
            else: 
                break

    for x in range(start_index,end_index+1):
        dates += [row[x]]
    return dates

# county must be full name
# state must be full name, not abbrev ex. "New Jersey", not "NJ"
# returns number of deaths in a county
def get_total_county_death_data(county,state):
    # reader for the csv file
    deaths_by_county = open('CSSEGIS-COVID-19/time_series_covid19_deaths_US.csv','r')
    deaths_by_county_reader = csv.reader(deaths_by_county)
    # column headers    
    row = next(deaths_by_county_reader)
    try:
        while row and not (row[5] == county and row[6] == state):
            row = next(deaths_by_county_reader)
    except StopIteration:
        print("death data not found for",county,'county',state)
        deaths_by_county.close()
        return None
    # print('Deaths in',county,'county,',state,':',row[len(row)-1])
    deaths_by_county_reader.close()
    return row[len(row)-1]

# county must be full name
# state must be full name, not abbrev ex. "New Jersey", not "NJ"
# start_date must be no earlier than 1/22/20, following format MM/DD/YY
# end_date must be no later than 6/23/20, following format MM/DD/YY (inclusive) (most recent date in time_series_covid19_deaths_US.csv)
#     ^^ (this date will change as the most up-to-date csv is redownloaded from github)
# returns number of deaths in a county between start_date and end_date, returns None if parameters are invalid
def get_county_death_data(county,state,start_date,end_date):
    # reader for the csv file
    deaths_by_county = open('CSSEGIS-COVID-19/time_series_covid19_deaths_US.csv','r')
    deaths_by_county_reader = csv.reader(deaths_by_county)

    start_date_split = [int(s) for s in start_date.split("/")]
    end_date_split = [int(e) for e in end_date.split("/")]

    if(not valid_date(start_date)):
        print("invalid start date:",start_date)
        pass
    elif(not valid_date(end_date)):
       print("invalid end date:",end_date)
    else:
        # column headers    
        row = next(deaths_by_county_reader)
        column_headers = row

        start_index = 0
        end_index = 0
        # 12 is the first column of daily death counts in the csv
        for x in range(12,len(column_headers)):
            # month,day,year
            date = [int(d) for d in column_headers[x].split('/')]

            if(start_date_split == date):
                start_index = x
            elif(end_date_split == date):
                end_index = x

            if(start_index > 0 and end_index > 0):
                if(start_index > end_index):
                    print("end date is chronologically before start date:",start_date,end_date)
                    return None
                else: 
                    break
        deaths = []

        try:
            while row and not (row[5] == county and row[6] == state):
                row = next(deaths_by_county_reader)
        except StopIteration:
            print("death data not found for",county,'county',state)
            deaths_by_county.close()
            return None
        # print('Deaths in',county,'county,',state,':',row[len(row)-1])

        for x in range(start_index,end_index+1):
            deaths += [row[x]]
        deaths_by_county.close()
        return deaths

# state must be full name ex: "New Jersey" NOT "NJ"
# date must be no earlier than 1/22/20 and no later than 6/23/20 (or the most recent date w data)
# returns dictionary of state's covid19 death data by county for a single date in time
# {"County State" : county covid-deaths}, ex. {"Atlantic NJ", ###}, returns None if parameters are invalid
# NOTE: sometimes the total deaths from this function are different than total deaths in get_death_by_district because there are rows with deaths not based in a county, some for a city etc.
def get_state_death_data(state,date):
    if(not valid_date(date)):
        print("date not valid",date)
        return None

    deaths_by_county = open('CSSEGIS-COVID-19/time_series_covid19_deaths_US.csv','r')
    deaths_by_county_reader = csv.reader(deaths_by_county)
    # column headers    
    row = next(deaths_by_county_reader)
    column_headers = row

    date_index = 0
    date_split = [int(d) for d in date.split("/")]
    for x in range(12,len(column_headers)):
        col_date = [int(c) for c in column_headers[x].split("/")]
        if(col_date == date_split):
            date_index = x
            break

    deaths_data = {}
    try:
        while row:
            if(state == row[6]):
                key_name = (str(row[5])+" "+str(state_abbrev[state])).lower()
                deaths_data[key_name] = int(row[date_index])
            row = next(deaths_by_county_reader)
    except StopIteration:
        deaths_by_county.close()
        return deaths_data

    deaths_by_county.close()
    return deaths_data

# county_info is 2D array, each row: [county name,state,county covid-deaths]
# state must be full name, not abbrev ex. "New Jersey", not "NJ"
# date must be no earlier than 1/22/20 and no later than the most recent day on time.....csv (MM/DD/YY)
# returns dictionary containing congressional districts and their death counts
# death count by district is based on proportion of county's population in district on a certain day
def get_death_by_district(state,date):
    if(not valid_date(date)):
        return None

    global not_counties
    districts = {}
    district_data = open('states_and_districts/'+ state_abbrev[state] +'-county-to-district.csv','r')

    district_reader = csv.reader(district_data)
    
    # column headers
    # 1: district #, 2: county name (ex: "Atlantic NJ"), 3: pop, 4: afact
    row = next(district_reader)
    row = next(district_reader)
    row = next(district_reader)
    deaths_by_county = get_state_death_data(state,date)
    try:
        while row: 
            county_name = row[2].lower()

            # for Alaska and Louisiana, remove Parish, Borough and Census Area from name
            tokens = word_tokenize(county_name)
            filtered = [w for w in tokens if not (w == 'parish' or w == 'borough' or w == 'census' or w == 'area')]
            county_name = ""
            for w in filtered:
                county_name += (w + " ")
            county_name = county_name[0:len(county_name)-1]

            cong_district = int(row[1])
            afact = float(row[4])
            try:
                if(cong_district == 0):
                    cong_district = 1
                if(cong_district in districts):
                    districts[cong_district] += round(deaths_by_county[county_name]*afact)
                else:
                    districts[cong_district] = round(deaths_by_county[county_name]*afact)
            except KeyError:
                not_counties[county_name] = 1
            row = next(district_reader)
    except StopIteration:
        return districts
    return districts

def get_death_by_district_over_time(state,start_date,end_date):
    if(not valid_date(start_date)):
        print("invalid start date:",start_date)
        return None
    if(not valid_date(end_date)):
        print("invalid end date:",end_date)
        return None

    start_date_death_counts = get_death_by_district(state,start_date)
    district_count = len(start_date_death_counts)
    death_counts = {}
    for x in range(1,district_count+1):
        death_counts[x] = [start_date_death_counts[x]]

    date_list = dates_between(start_date,end_date)[1:] # already took care of start_date in creating death_counts
    for date in date_list:
        deaths = {k : v for k, v in sorted(get_death_by_district(state,date).items())}
        for k,v in deaths.items():
            death_counts[k] += [v]

    return death_counts

# ALL STATES
def get_all_deaths_by_district_over_time(start_date,end_date):
    if(not valid_date(start_date)):
        print("invalid state date:",start_date)
        return None
    if(not valid_date(end_date)):
        print("invalid end date:",end_date)
        return None

    print("Creating csv of deaths by Congressional District between",start_date,"and",end_date,"...")
    file = open('deaths_by_district/deaths_by_district_'+start_date.replace("/","_")+'_to_'+end_date.replace("/","_")+'.csv','w',newline='')

    writer = csv.writer(file)
    writer.writerow(['state','district']+dates_between(start_date,end_date))

    states = list(state_abbrev.keys())

    for state in states:
        print(state)
        death_counts = get_death_by_district_over_time(state,start_date,end_date)
        districts = len(death_counts)
        for d in range(1,districts+1):
            writer.writerow([state,d]+death_counts[d])
    
    file.close()

if __name__ == '__main__':
    # Downloads most recent version of Johns Hopkins COVID19 death data
    url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
    r = requests.get(url, allow_redirects=True)

    f = open('CSSEGIS-COVID-19/time_series_covid19_deaths_US.csv', 'wb')
    f.write(r.content)

    
    get_all_deaths_by_district_over_time("6/23/20","7/6/20")
    '''
    #print(get_death_by_district_over_time("Louisiana","4/20/20","4/26/20"))

    #print(get_state_death_data("Alaska","4/20/20"))
    
    deaths_by_district = open('deaths_by_district/deaths_by_district.csv','w',newline='\n')

    district_writer = csv.writer(deaths_by_district)
    district_writer.writerow(['state','district','deaths'])
    states = list(state_abbrev.keys())
    
    for state in states:
        # key = district : value = death count
        state_deaths_by_district = {k : v for k, v in sorted(get_death_by_district(state,"6/23/20").items())}
        total = 0
        for k,v in state_deaths_by_district.items():
            district_writer.writerow([state,k,v])
            total += v
        print(state,":",total)

    #print(list(not_counties.keys()))
    '''

    '''
    nj_deaths_by_district = (get_death_by_district("New Jersey"))
    
    nj_deaths_by_district = {k : v for k,v in sorted(nj_deaths_by_district.items())}
    print(nj_deaths_by_district) 
    total1 = 0
    for k,v in nj_deaths_by_district.items():
        total1+=v

    nj_state = get_state_death_data("New Jersey")
    total2 = 0
    for k,v in nj_state.items():
        total2+=v 

    print(total1,total2) 
    # they're off bc of bergen, essex, passaic, and union counties

    ms_deaths_by_district = (get_death_by_district("Missouri"))
    
    ms_deaths_by_district = {k : v for k,v in sorted(ms_deaths_by_district.items())}
    print(ms_deaths_by_district)
    total1 = 0
    for k,v in ms_deaths_by_district.items():
        total1+=v

    ms_state = get_state_death_data("Missouri")
    total2 = 0
    for k,v in ms_state.items():
        total2+=v 

    print(total1,total2) 
    # off bc of Kansas City, 31 deaths in city alone
    # the city falls in many counties?? and 4,5,6 cong. district
    '''
    #deaths_by_district.close()