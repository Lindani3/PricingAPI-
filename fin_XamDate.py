# -*- coding: utf-8 -*-
"""
Created on Sun Jun  9 23:09:04 2024

@author: Lindani Hlophe
"""

'''
We set this class to either querry data Directy from the NagarAPI 
or it can just reat it as a csv file 

'''
import pandas as pd
from nagerapi import NagerObjectAPI
from enum import Enum
import enum
from datetime import datetime, date, timedelta
import calendar
from dateutil.relativedelta import relativedelta
import math
import numpy as np


class Calendar:
    
    # Class variable to get the date at which the data was retrieved 
    retrieval_datetime = None
    availableCountries = None 
    
    def __init__(self, countryCode):
        self.countryCode = countryCode.split("+")
        self.holidayData = Calendar.loadHoliday(self.countryCode, "public_holidays_by_year_latest.csv")
        #self.weekendType = Calendar.loadWeekendType("weekend_csv_path.csv")
        self.weekendTypes = self.loadWeekend("countryWeekendTypes.csv")         
    
    @classmethod
    def loadHoliday(cls, countryCode, path):
        holidaysDf = pd.read_csv(path)
        holidaysDf["date"] = pd.to_datetime(holidaysDf['date']).dt.date
        
        
        # Convert countryCode to uppercase and filter the DataFrame
        countryCodes = [country.upper() for country in countryCode]
        
        #Validate Country Code
        countryCodes = cls.isValidCountryCode(countryCodes, holidaysDf)
        Calendar.availableCountries = set(holidaysDf["countryCode"].unique())
        
        filterData = holidaysDf[holidaysDf['countryCode'].isin(countryCodes)]
        # Extraction Date 
        Calendar.retrieval_datetime = (pd.to_datetime(holidaysDf['extraction_date']).iloc[0])
        
        return filterData[['date','name','countryCode']]
    
    @classmethod
    def loadWeekend(cls,path):
        weekend_data = pd.read_csv(path)
        #weekend_data['Country Code'] = weekend_data['Country Code'].astype(str).str.lower()
        
        weekend_mapping = {
            "Saturday-Sunday": (5, 6),  # Saturday is 5, Sunday is 6 (in Python's weekday indexing)
            "Friday-Saturday": (4, 5),  # Friday is 4, Saturday is 5
            "Thursday-Friday": (3, 4)   # Weekends falling on Thursday and Friday
        }

        country_weekends = {}
        for _, row in weekend_data.iterrows():
            country_code = row["Country Code"]
            weekend_type = row["Weekend Type"]
            if weekend_type in weekend_mapping:
                country_weekends[country_code] = weekend_mapping[weekend_type]
            else:
                raise ValueError(f"Unknown weekend type: {weekend_type}")
        
        return country_weekends
        
    @classmethod
    def isValidCountryCode(cls, countryCodes, holidaysDf):
        availableCountries = set(holidaysDf["countryCode"].unique())
        countryCodes = [country.upper() for country in countryCodes]
        invalidCountryCodes = [cc for cc in countryCodes if cc not in availableCountries]
        if invalidCountryCodes:
            raise ValueError("Invalid Country code ", invalidCountryCodes)
        return countryCodes
    
    
    def isWeekend(self, givenDate):
        
        if givenDate < date(2020,1,1) or givenDate > date(2056,12,31):
            raise ValueError("The given date is outside the allowed range (2020-01-01 to 2056-12-31).")
            
            
        countryCodes = self.isValidCountryCode(self.countryCode, self.holidayData)

        for country in countryCodes:
                        
            if country in self.weekendTypes:
                #print(country, " "   ,self.weekendTypes[country])
                #print("Day of the week ", givenDate.weekday())
                if givenDate.weekday() in self.weekendTypes[country]:
                    return False
            else:
                raise ValueError(f"Weekend information not available for country code: {countryCodes}")
        return True
    
    # Check if it a business day in a particular country  
    def isBusinessDay(self, given_date):
        country_codes = self.countryCode
        for code in country_codes:
            if not self.isWeekend(given_date):
                return False
            if given_date in self.holidayData['date'].values:
                return False
        return True   

    #return holidaysBetween 
    def getHolidaysData(self,startDate,endDate):
        if startDate < date(2020,1,1) or startDate > date(2056,12,31):
            raise ValueError("The given start date is outside the allowed range (2020-01-01 to 2056-12-31).")
         
        elif endDate < date(2020,1,1) or endDate > date(2056,12,31):
            raise ValueError("The given end date is outside the allowed range (2020-01-01 to 2056-12-31).")
         
        if startDate < endDate:
            raise ValueError("start Year must be less than end year")
        
        
        # Filter the public holidays within the specified range for the given country
        filteredHolidays = self.holidayData[
            (self.holidayData["date"] >= startDate) &
            (self.holidayData["date"] <= endDate)
        ]
        return filteredHolidays

    '''
        Allow negative businessDays
        Input startRoll = NAN do not adjust if startDay is on a holiday
        > add a default input to adjust the startDate if it not a business day 
        > startDate roll
        
    '''

    # add number of business >> addBusinessDay(self,startDate,roll=NAN,numBusinessDay)
    
    def addBusinessDays(self, startDate, numBusinessDays):
        
        if numBusinessDays < 0:
            raise ValueError(f"Number of business days must be 0 or more, given: {numBusinessDays}")
            
        # Start with the initial date
        currentDate = startDate
        businessDaysAdded = 0  # Counter for the number of business days added
    
        # If the given date is not a business day and no business days are to be added,
        # find the next business day
        if numBusinessDays == 0 and not self.isBusinessDay(currentDate):
            while not self.isBusinessDay(currentDate):
                currentDate += timedelta(days=1)  # Move to the next day
            return currentDate  # Return the first business day
    
    
        # Loop until the required number of business days are added
        while businessDaysAdded < numBusinessDays:
            currentDate += timedelta(days=1)  # Increment by one calendar day
            if self.isBusinessDay(currentDate):  # If it's a business day
                businessDaysAdded += 1  # Increment the business days count
    
        return currentDate
 
    # Define a function to find the last business day in a given month
    def getLastBusinessDateInMonth(self, givenDate):
        
        """
        Finds the last business day in a given month for specified countries.
        """
        
        # Determine the last day of the month
        lastDayOfMonth = calendar.monthrange(givenDate.year, givenDate.month)[1]  # Get the last day number
        lastDate = datetime(givenDate.year, givenDate.month, lastDayOfMonth).date()  # Construct the last date
        
        # Backtrack to find the last business day in the month
        while not self.isBusinessDay(lastDate):  # If the last day isn't a business day
            lastDate -= timedelta(days=1)  # Move backward by one day
        
        return lastDate  # Return the last business dayt
    

    # Function to determine if a given date is the last business day of its month
    def isLastBusinessDayInMonth(self, givenDate):
        lastBusinessDate = self.getLastBusinessDateInMonth(givenDate)
        if lastBusinessDate == givenDate:
            return True
        else:
                return False


    
    def addTenor(self, startDate, tenor, roll, preserveMonthEnd):
        """
        Adds a specified tenor (in days, weeks, months, or years) to the start date,
        and adjusts non-business days according to the specified roll method.
        """
        tenor = tenor.lower()
        
        # Validate the start date
        if not isinstance(startDate, date):
            raise ValueError("The 'startDate' must be a datetime.date object.")
    
        # Validate the roll parameter
        valid_rolls = {"f", "p", "mf", "mp"}
        roll = roll.lower()  # Normalize the roll to lowercase
        if roll not in valid_rolls:
            raise ValueError(f"Invalid roll type: '{roll}'. Expected 'f', 'p', 'mf', or 'mp'.")
    
        # Validate the preserveMonthEnd parameter
        if isinstance(preserveMonthEnd, str):
            preserveMonthEnd = preserveMonthEnd.strip().lower()  # Normalize and trim whitespace
            if preserveMonthEnd == "true":
                preserveMonthEnd = True
            elif preserveMonthEnd == "false":
                preserveMonthEnd = False
            else:
                raise ValueError("The 'preserveMonthEnd' parameter must be 'True' or 'False'.")
        elif not isinstance(preserveMonthEnd, bool):
            raise ValueError("The 'preserveMonthEnd' parameter must be 'True' or 'False'.")
    
        # Determine the raw end date based on the tenor
        unit = tenor[-1]  # Last character indicates the unit (d, w, m, y)
        amount = int(tenor[:-1])  # The number preceding the unit indicates the amount
    
        if unit == "d":
            rawEndDate = startDate + timedelta(days=amount)
        elif unit == "w":
            rawEndDate = startDate + timedelta(weeks=amount)
        elif unit == "m":
            rawEndDate = startDate + relativedelta(months=amount)
        elif unit == "y":
            rawEndDate = startDate + relativedelta(years=amount)
        else:
            raise ValueError(f"Invalid tenor unit: '{unit}'. Expected 'd', 'w', 'm', or 'y'.")
    
        # If preserveMonthEnd is True and the start date is the last business day of its month,
        # adjust the rawEndDate to the last business day of the new month
        if preserveMonthEnd and (unit in ("m", "y")):
            if self.isLastBusinessDayInMonth(startDate):
                rawEndDate = self.getLastBusinessDateInMonth(rawEndDate)
    
        # Roll adjustment based on the specified roll method
        if self.isBusinessDay(rawEndDate):
            finalEndDate = rawEndDate
        else:
            # Handle the different roll behaviors
            if roll == "f":  # Following
                finalEndDate = self.addBusinessDays(rawEndDate, 0)  # Move to the next business day
            elif roll == "p":  # Preceding
                while not self.isBusinessDay(rawEndDate):
                    rawEndDate -= timedelta(days=1)  # Move backward
                finalEndDate = rawEndDate
            elif roll == "mf":  # Modified Following
                finalEndDate = self.addBusinessDays(rawEndDate, 0)  # Move to the following business day
                if finalEndDate.month != rawEndDate.month:  # If in a different month, roll backward
                    finalEndDate -= timedelta(days=1)
                    while not self.isBusinessDay(finalEndDate):
                        finalEndDate -= timedelta(days=1)
            elif roll == "mp":  # Modified Preceding
                finalEndDate = rawEndDate
                while not self.isBusinessDay(rawEndDate):
                    finalEndDate = rawEndDate
                    rawEndDate -= timedelta(days=1)  # Move backward
    
                if finalEndDate.month != rawEndDate.month:
                    finalEndDate = self.addBusinessDays(finalEndDate+timedelta(days=1), 0)  # Move forward
            else:
                raise ValueError(f"Invalid roll type: '{roll}'. Expected 'f', 'p', 'mf', or 'mp'.")
    
        return finalEndDate


class Date(date):
    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str):
            try:
                dt = datetime.strptime(args[0], "%Y-%m-%d")
                return date.__new__(cls, dt.year, dt.month, dt.day)
            except ValueError:
                raise ValueError("Invalid date format. Use 'YYYY-MM-DD'.")
        elif len(args) == 3:
            return date.__new__(cls, *args)
        else:
            raise ValueError("Invalid arguments. Use 'YYYY-MM-DD' or (YYYY, MM, DD).")
          
    def isLeapYear(self):
        return calendar.isleap(self.year)

    @staticmethod
    def daysInYear(year):
        return 366 if calendar.isleap(year) else 365


class Compounding(Enum):
    ANNUALLY = "NACA"
    SEMIANNUALLY = "NACS"
    QUARTERLY = "NACQ"
    MONTHLY = "NACM"
    CONTINUOUSLY = "NACC"
    
    @classmethod
    def frm_string(cls, comp_str):
        normalized_str = comp_str.strip().upper()
        for comp in cls:
            if comp.value == normalized_str:
                return comp
        raise ValueError(f"Invalid Compounding: {comp_str}")

    @staticmethod
    def getPeriodsPerYear(comp_enum): # Frequency Here 
        if comp_enum == "NACA":
            return 1
        elif comp_enum == "NACS":
            return 2
        elif comp_enum == "NACQ":
            return 4
        elif comp_enum == "NACM":
            return 12
        elif comp_enum == "NACW":
            return 52
        elif comp_enum == "NACD":
            return 365
        elif comp_enum == "NACC":
            return 1

class DayCountConvention(enum.Enum):
    ACT_365 = 'act/365'
    ACT_360 = 'act/360'
    
    @classmethod
    def from_string(cls, basis_str):
        normalized_str = basis_str.strip().lower()
        for basis in cls:
            if basis.value == normalized_str:
                return basis
        raise ValueError(f"Invalid basis: {basis_str}")

class DayCountBasis:
    def __init__(self, basis):
        self.basis = DayCountConvention.from_string(basis)

    def dayCountFraction(self, start_date, end_date):
    
        if self.basis == DayCountConvention.ACT_365:
            return (end_date - start_date).days / 365.0
        elif self.basis == DayCountConvention.ACT_360:
            return (end_date - start_date).days / 360.0
        else:
            raise ValueError("Unsupported day count convention")
            
# fromFrac = DayCounFrcation(startDate,endDate,basis)
#toFrac = DayCountFraction(startDate,endDate,basis)


class Rate:
    def __init__(self, rate,fromFrac,compounding):
        self.rate = rate
        self.fromFrac = fromFrac # this should be geven by a contructor 
        self.compounding = compounding # this is should from a contructor 
    
      
        
    def equivalentRate(self,toCompounding,toFrac):
        toComp_enum = Compounding.frm_string(toCompounding)
        
        NAC_ = ["NACA","NACM","NACW","NACD","NACQ","NACS"]
        x = Compounding.getPeriodsPerYear(self.compounding)
        y = Compounding.getPeriodsPerYear(toCompounding)
        
        if self.compounding in NAC_ and toCompounding != "NACC":
           
            num = self.fromFrac*x
            dem = toFrac*y
            return (((1+self.rate/x)**(num/dem))-1)*y
    
        elif self.compounding == "NACC":

            return y*(math.exp((self.rate*self.fromFrac)/(y*toFrac)) -1)
    
        elif toCompounding == "NACC" and self.compunding in NAC_:
            return math.log((1+self.rate/x)**(x*self.fromFrac))/(toFrac)
        
        
    def discountFactor(self,dayFraction):
        
        yearFrac = dayFraction
        
        n = Compounding.getPeriodsPerYear(self.compounding)
        
        if self.compounding == "NACC":
            return math.exp(-self.rate*yearFrac)
        else:
            discountFactor = 1 / ((1 + self.rate / n) ** (n * yearFrac))
        
        return discountFactor 
    
        
        
        
        