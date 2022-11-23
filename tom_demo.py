import json
import pandas
# import numpy
from dateutil import parser

# import subprocess
import os
from os.path import exists

import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


OUTPUT_DIRECTORY = "ExtractedTables"
Tom_url = "https://www.tomitribe.com/legal/lifecycle-policy/"

def getAnnouncementURL(json_dump_data,row):
    """
    Reads the dumped json for product links.
    """
    response = json.loads(json_dump_data.at[row,'RAW_announcement_url_results'])
    search_results = response['items']
    link_list = []
    for result in search_results:
        link_list.append(result['link'])
    return link_list

def randomWaitBetween(low,high,reason):
    wait = random.randrange(low,high, 1)
    #print('_'*25,f"\n\nWaiting {wait} seconds {reason}\n",'_'*25,"\n")
    return wait

def removeSpaces(text):
    return text.replace(" ", "_")

def parseDate(text):
    try:
        date = parser.parse(text)
        return date.strftime('%Y-%m-%d')
    except Exception as e:
        return text

class TableScraper():
    def __init__(self):
        # self.driver = webdriver.Safari()
        # self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.driver = webdriver.Chrome("./chromedriver")


    def closeBrowser(self):
        self.driver.quit()

    def closeTab(self):
        self.driver.close()

    def focusTab(self,number):
        focus_page = self.driver.window_handles[number]
        self.driver.switch_to.window(focus_page)

    def newTab(self):
        current_tab = self.driver.current_window_handle
        self.driver.execute_script("window.open('');")
        all_tabs = self.driver.window_handles
        for tab in all_tabs:
            if tab != current_tab:
                self.driver.switch_to.window(tab)
                break

    def getSoftwareNames(self):
        s_name = []
        names = self.driver.find_elements(By.XPATH,".//strong")
        for name in names[4:]:
            # print(name.text.replace(" Lifecycle Dates",""))
            my_var = name.text.replace(" Lifecycle Dates","")
            s_name.append(my_var)  
        print(s_name)


    def detectTable(self,link):
        self.driver.get(link)
        time.sleep(1)
        tables = self.driver.find_elements(By.XPATH,"//table")
        total = len(tables[1:])
        return total


    def detectDate(self):
        all_text = scraper.driver.find_element(By.XPATH,"//body").text
        all_text = all_text.replace('\n',' ')
        words = all_text.split()
        for word in words:
            try:
                date = parseDate(word.lstrip().rstrip())
                # print(date)
                return True
            except:
                pass
        return False


    def getListOfRows(self,webElement):
        list_of_rows = []
        trs = webElement.find_elements(By.XPATH,".//tr")

        for tr in trs:

            row_as_list = []
            ths = tr.find_elements(By.XPATH,".//th")
            for th in ths:
                row_as_list.append(th.text)
            list_of_rows.append(row_as_list)

            row_as_list = []
            tds = tr.find_elements(By.XPATH,".//td")
            for td in tds:
                row_as_list.append(td.text)
            list_of_rows.append(row_as_list)

        return list_of_rows

    def extractTable(self,link_number,link):

        final_datalist = []
        list_of_tables = self.driver.find_elements(By.XPATH,"//table")
        table_number = 0
        for table in list_of_tables[1:]:
            dataframe = pandas.DataFrame()

            list_of_rows = []

            theads = table.find_elements(By.XPATH,".//thead")
            tbodys = table.find_elements(By.XPATH,".//tbody")
            tfoots = table.find_elements(By.XPATH,".//tfoot")

            for thead in theads:
                list_of_rows = self.getListOfRows(thead)
            thead_dataframe = pandas.DataFrame(list_of_rows)
            list_of_rows = []

            for tbody in tbodys:
                list_of_rows = self.getListOfRows(tbody)
            tbody_dataframe = pandas.DataFrame(list_of_rows)
            list_of_rows = []

            for tfoot in tfoots:
                list_of_rows = self.getListOfRows(tfoot)
            tfoot_dataframe = pandas.DataFrame(list_of_rows)

            dataframe = pandas.concat([thead_dataframe,tbody_dataframe,tfoot_dataframe])

            dataframe.dropna(inplace = True)
            dataframe.columns = dataframe.iloc[0]
            dataframe = dataframe.iloc[1: , :]
            dataframe['announcement_url'] = link

            table_number += 1
            # dataframe.to_csv(f"{OUTPUT_DIRECTORY}/link_{link_number}_table_{table_number}.csv",index=False)
            # del(dataframe)
        
            final_datalist.append(dataframe)

        final = pandas.concat(final_datalist)
        # print(len(final.index))
        # final.to_csv(f"{OUTPUT_DIRECTORY}/Final_Datalist.csv",index=False)
        # print(final)

        print(f"{table_number} Eligible found and written.")


    def getTableAsDataframe(self,table,link):
        list_of_rows = []

        rename_dict = {
        "Family":["version"],
        "Start":["FULL SUPPORT","MAINTENANCE SUPPORT","EXTENDED SUPPORT"],
        "End":["FULL SUPPORT","MAINTENANCE SUPPORT","EXTENDED SUPPORT"],
        }

        theads = table.find_elements(By.XPATH,".//thead")
        tbodys = table.find_elements(By.XPATH,".//tbody")
        tfoots = table.find_elements(By.XPATH,".//tfoot")

        for thead in theads:
            list_of_rows = self.getListOfRows(thead)
        thead_dataframe = pandas.DataFrame(list_of_rows)
        list_of_rows = []

        for tbody in tbodys:
            list_of_rows = self.getListOfRows(tbody)
        tbody_dataframe = pandas.DataFrame(list_of_rows)
        list_of_rows = []

        for tfoot in tfoots:
            list_of_rows = self.getListOfRows(tfoot)
        tfoot_dataframe = pandas.DataFrame(list_of_rows)

        dataframe = pandas.concat([thead_dataframe,tbody_dataframe,tfoot_dataframe])

        dataframe.dropna(inplace = True)
        dataframe.columns = dataframe.iloc[0]
        dataframe = dataframe.iloc[1: , :]
        dataframe['announcement_url'] = link

        dataframe.rename(columns=lambda c: rename_dict[c].pop(0)+" "+c if c in rename_dict.keys() else c, inplace = True)

        # dataframe['Family'] = dataframe['Family'].replace(".x","",regex=True)
        return dataframe

    def getTable(self, table_number, link):
        """
        Get's the first table from Cisco link which contains all the dates
        and returns it as a pandas dataframe
        """
        list_of_tables = self.driver.find_elements(By.XPATH,"//table")
        table = list_of_tables[table_number-1]
        return self.getTableAsDataframe(table,link)


    def addASoftwareColumn(self, sw_name_element, table_element):
        table_as_dataframe = self.getTableAsDataframe(table_element,Tom_url)
        table_as_dataframe["Software Name"] = sw_name_element.text.replace(" Lifecycle Dates","")
        # print(table_as_dataframe.columns)
        return table_as_dataframe


    def fixDateFormats(self,dataframe):
        dataframe = dataframe.astype(str)
        dataframe['FULL SUPPORT Start'] = dataframe.apply(lambda row : parseDate(row ['FULL SUPPORT Start']), axis=1)
        dataframe['MAINTENANCE SUPPORT Start'] = dataframe.apply(lambda row : parseDate(row ['MAINTENANCE SUPPORT Start']), axis=1)
        dataframe['EXTENDED SUPPORT Start'] = dataframe.apply(lambda row : parseDate(row ['EXTENDED SUPPORT Start']), axis=1)
        dataframe['FULL SUPPORT End'] = dataframe.apply(lambda row : parseDate(row ['FULL SUPPORT End']), axis=1)
        dataframe['MAINTENANCE SUPPORT End'] = dataframe.apply(lambda row : parseDate(row ['MAINTENANCE SUPPORT End']), axis=1)
        dataframe['EXTENDED SUPPORT End'] = dataframe.apply(lambda row : parseDate(row ['EXTENDED SUPPORT End']), axis=1)

        return dataframe


if not exists(OUTPUT_DIRECTORY):
    print("Creating output directory...")
    os.mkdir(OUTPUT_DIRECTORY)
    print("Done.")

# link_list = input("Enter comma seperated links to extract tables from: ")
# link_list = link_list.split(',')
# link_list = [
# #Protocols
# "https://www.tomitribe.com/legal/lifecycle-policy/"
# ]


scraper = TableScraper()

#Go to 
scraper.driver.get(Tom_url)

software_names = scraper.driver.find_elements(By.XPATH,"//strong")

software_names = software_names[4:]

len(software_names)

tables = scraper.driver.find_elements(By.XPATH,"//table[@class='tt-table tt-table-dark']")

len(tables)

list_of_dataframes = []

for sw_name, table in zip(software_names,tables):
    dataframe = scraper.addASoftwareColumn(sw_name,table)
    dataframe = scraper.fixDateFormats(dataframe)
    list_of_dataframes.append(dataframe)

TOM_data = pandas.concat(list_of_dataframes)

# rename_dict = {
# "Family":["version"],
# "Start":["FULL SUPPORT","MAINTENANCE SUPPORT","EXTENDED SUPPORT"],
# "End":["FULL SUPPORT","MAINTENANCE SUPPORT","EXTENDED SUPPORT"],
# }

s_name = TOM_data.pop('Software Name')
TOM_data.insert(0, 'Software Name', s_name)


# TOM_data.rename(columns=lambda c: rename_dict[c].pop(0)+" "+c if c in rename_dict.keys() else c, inplace = True)

# TOM_data['FULL SUPPORT Start']=pandas.to_datetime(TOM_data['FULL SUPPORT Start'])
# TOM_data['MAINTENANCE SUPPORT Start']=pandas.to_datetime(TOM_data['MAINTENANCE SUPPORT Start'])
# TOM_data['EXTENDED SUPPORT Start']=pandas.to_datetime(TOM_data['EXTENDED SUPPORT Start'])
# TOM_data['FULL SUPPORT End']=pandas.to_datetime(TOM_data['FULL SUPPORT End'])
# TOM_data['MAINTENANCE SUPPORT End']=pandas.to_datetime(TOM_data['MAINTENANCE SUPPORT End'])
# TOM_data['EXTENDED SUPPORT End']=pandas.to_datetime(TOM_data['EXTENDED SUPPORT End'])


# TOM_data.to_csv(f"{OUTPUT_DIRECTORY}/TOM_data2.csv",index=False)
TOM_data.to_csv("TOM_data3.csv",index=False)




# rename_dict = {
# "Software Name":["name"],
# "Family":["version"],
# "Start":["FULL SUPPORT","MAINTENANCE SUPPORT","EXTENDED SUPPORT"],
# "End":["FULL SUPPORT","MAINTENANCE SUPPORT","EXTENDED SUPPORT"],
# }

# TOM_data.rename(columns=lambda c: rename_dict[c].pop(0) if c in rename_dict.keys() else c)
# TOM_data.rename(columns=lambda c: rename_dict[c].pop(0) + c if c in rename_dict.keys() else c, inplace = True)


# for link in link_list:
#     print(scraper.detectTable(link)," detected")
#     scraper.extractTable(link_list.index(link),link)
#     scraper.getSoftwareNames()
#     print(f"Completed {link_list.index(link)+1} of {len(link_list)}")

# scraper.closeBrowser()
