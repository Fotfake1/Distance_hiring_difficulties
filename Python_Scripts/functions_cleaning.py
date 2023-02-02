# Import the required libraries
from zipfile import ZipFile
import pandas as pd
import numpy as np
import os
import pickle
import sys
import plotly.express as px
import plotly.graph_objects as go
import fuzzywuzzy as fw
from fuzzywuzzy import fuzz

# import seaborn as sns
import openpyxl

# from functions_cleaning import *
import geopy
from geopy import distance
import statsmodels.formula.api as sm
from scipy.stats import linregress


def __delete_rows_with_unique_values(dataframe, column_name):
    """
    This function should clean the the city name column of
    the scraped dataset.
    Delete the rows, which have an NA for the location of
    the organization.

    Input:
    - dataframe: Pandas Dataframe
    - column_name: Name of the column which should be cleaned
    Raises:
    - Raises an error if the column does not exist
    """
    value_counts = dataframe[column_name].value_counts()
    dataframe = dataframe[
        dataframe[column_name].isin(value_counts.index[value_counts != 1])
    ]
    return dataframe


def __clean_duration(data):
    data["duration"] = pd.to_numeric(data["duration"], errors="coerce")
    # every observation above 365 is set as 365
    data = data.dropna(subset=["duration"])
    data.loc[data["duration"] > 365, "duration"] = 365
    data["log_duration"] = data["duration"].apply(np.log)
    return data


def __clean_posting_count(data):
    # posting count
    data["posting_count"] = pd.to_numeric(data["posting_count"], errors="coerce")
    data = data.dropna(subset=["posting_count"])
    # top code
    data.loc[data["posting_count"] > 20, "posting_count"] = 20
    return data


def __clean_contract_type(data):
    # only consider the following values
    data = data[
        (data["contract_type_label"] == "Permanent contract")
        | (data["contract_type_label"] == "Internship / Graduation position")
        | (data["contract_type_label"] == "Possibly permanent contract")
        | (data["contract_type_label"] == "Possibly permanent contract")
        | (data["contract_type_label"] == "Apprenticeship")
        | (data["contract_type_label"] == "Temporary contract")
        | (data["contract_type_label"] == "Secondment / Interim")
    ]

    # clustering 
    acceptable_values = [
        "Permanent contract",
        "Internship / Graduation position",
        "Possibly permanent contract",
    ]

    data["contract_type_label_cluster"] = np.where(
        data["contract_type_label"].isin(acceptable_values),
        "Permanent",
        "Non_Permanent",
    )
    # we now restrict the dataset to regular working hours only.
    data = data[data["working_hours_type_label"] == "Regular working hours"]
    return data


def __clean_salary_dummy(data):
    data["salary_dummy"] = data["salary"].notnull()
    return data


def __clean_advertiser_type_value(data):
    data = data.dropna(subset=["advertiser_type_label"])
    data = data[data["advertiser_type_label"] == "Direct employer"]
    return data


def __clean_profession_code(data):
    data = data.dropna(subset=["profession_isco_code_value"])
    data["profession_isco_code_value"] = pd.to_numeric(
        data["profession_isco_code_value"], errors="coerce"
    )
    return data


def __clean_job_ID(data):
    data = data.dropna(subset=["job_id"])
    data["job_id"] = pd.to_numeric(data["job_id"], errors="coerce")
    return data


def __clean_org_ID(data):
    data = data.dropna(subset=["organization_ID"])
    data["organization_ID"] = pd.to_numeric(data["organization_ID"], errors="coerce")
    return data


def __clean_working_hours(data):
    data = data[data["working_hours_type_label"] == "Regular working hours"]
    return data


def __clean_orga_industry_label(data):
    data = data.dropna(subset=["organization_industry_label"])
    return data


def __clean_language(data):
    # only consider the following values
    data = data[
        (data["language"] == "de")
        | (data["language"] == "en")
        | (data["language"] == "zh")
        | (data["language"] == "fr")
        | (data["language"] == "cs")
        | (data["language"] == "es")
        | (data["language"] == "nl")
        | (data["language"] == "hu")
        | (data["language"] == "sv")
        | (data["language"] == "no")
        | (data["language"] == "da")
        | (data["language"] == "sk")
        | (data["language"] == "ru")
        | (data["language"] == "pl")
        | (data["language"] == "pt")
        | (data["language"] == "it")
        | (data["language"] == "ro")
        | (data["language"] == "ja")
        | (data["language"] == "el")
    ]
    # cluster
    data["Applicant_language_cluster"] = np.where(
        data["language"] == "de", "German", "International"
    )
    return data


def __clean_education_level(data):
    #drop certain observations with "unbekannt" or "Grundschule"
    data = data.drop(data[data["education_level_label"] == "Unbekannt"].index)
    data = data.drop(data[data["education_level_label"] == "Grundschule"].index)
    university = ["Bachelor", "Master", "Dissertation"]
    data["education_level_cluster"] = np.where(
        data["education_level_label"].isin(university),
        "University degree",
        "Non university degree",
    )
    return data


def __clean_dates(data):
    # make the dates in the right dimension
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["quarter_of_date"] = data["date"].dt.quarter
    data["month_of_date"] = data["date"].dt.month
    return data


def __clean_firm_size(data):
    # only consider medium and big firms, clean all the NAN and "Unbekannt values"
    data = data.dropna(subset=["organization_size_label"])
    data = data[data["organization_size_label"] != "Unbekannt"]
    data = data[data["organization_size_label"] != "Unbekannt"]
    data = data[
        (data["organization_size_label"] == "5000+")
        | (data["organization_size_label"] == "1000-4999")
        | (data["organization_size_label"] == "500-999")
    ]
    return data


def __clean_isco_code(data):
    # Only consider numeric values, not missing values or strings
    data["profession_isco_code_value"] = pd.to_numeric(
        data["profession_isco_code_value"], errors="coerce"
    )
    # only consider meaningful values
    deletion_boolean_vector = data["profession_isco_code_value"] == 9999999999
    rows_to_drop = data.index[deletion_boolean_vector]
    data = data.drop(index=rows_to_drop)
    data["profession_isco_code_value_agg_1"] = pd.to_numeric(
        data["profession_isco_code_value"].apply(lambda x: str(x)[:3])
    )
    data["profession_isco_code_value_agg_2"] = pd.to_numeric(
        data["profession_isco_code_value"].apply(lambda x: str(x)[:2])
    )
    return data


def full_dataset_cleaning(dataset):
    # call the individual cleaning steps in one function. 
    data = dataset
    data = __delete_rows_with_unique_values(
        dataframe=data, column_name="organization_location_name"
    )
    data = __clean_duration(data=data)
    data = __clean_posting_count(data=data)
    data = __clean_contract_type(data=data)
    data = __clean_salary_dummy(data=data)
    data = __clean_advertiser_type_value(data=data)
    data = __clean_profession_code(data=data)
    data = __clean_job_ID(data=data)
    data = __clean_org_ID(data=data)
    data = __clean_working_hours(data=data)
    data = __clean_orga_industry_label(data=data)
    data = __clean_language(data=data)
    data = __clean_education_level(data=data)
    data = __clean_dates(data=data)
    data = __clean_firm_size(data=data)
    data = __clean_isco_code(data=data)
    return data
