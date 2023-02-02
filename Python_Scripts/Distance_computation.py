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
import functions_distance as dcf


used_columns = [
    "organization_location_name",
    "advertiser_type_value",
    "advertiser_type_label",
    "posting_count",
    "date",
    "duration",
    "via_intermediary",
    "language",
    "job_title",
    "profession_value",
    "profession_isco_code_value",
    "profession_isco_code_label",
    "location",
    "location_name",
    "region_value",
    "region_label",
    "education_level_value",
    "education_level_label",
    "contract_type_value",
    "contract_type_label",
    "working_hours_type_value",
    "working_hours_type_label",
    "hours_per_week_from",
    "hours_per_week_to",
    "salary",
    "organization_industry_value",
    "organization_industry_label",
    "organization_size_value",
    "organization_size_label",
    "location_coordinates",
    "organization_ID",
    "contract_type_label_cluster",
    "salary_dummy",
    "Applicant_language_cluster",
    "education_level_cluster",
    "quarter_of_date",
    "month_of_date",
    "log_duration",
    "Latitudal_coordinates_organization",
    "Longitudinal_coordinates_organization",
    "Fuzzy_Rating",
    "latitudal_coordinates_job",
    "longitudinal_coordinates_job",
    "distance_between_job_and_organization",
    "profession_isco_code_value_agg_1",
    "profession_isco_code_value_agg_2",
]

np.set_printoptions(threshold=sys.maxsize)
# Paths for accessing files dynamically
sub_path = os.getcwd()
path_cwd = os.path.dirname(sub_path)
path_dta_cleaned = os.path.join(path_cwd, "Data_cleaned")
path_dta = os.path.join(path_cwd, "Data")

# read in the paths
data = pd.DataFrame(pd.read_csv(path_dta_cleaned + "/vacancies_cleaned.csv"))
city_gps_match_data = pd.DataFrame(pd.read_excel(path_dta + "/Cities_gps.xlsx"))

data = dcf.create_distance_measures(
    data=data, city_gps_match_data=city_gps_match_data, used_columns=used_columns
)
filepath = "/Users/luisenriquekaiser/Desktop/Inhalte/Uni_Bonn/Seminar/Project/Data_cleaned/dataset_final.xlsx"
# if not os.path.exists(os.path.dirname(filepath)):
#    os.makedirs(os.path.dirname(filepath))
data[0].to_excel(filepath)
