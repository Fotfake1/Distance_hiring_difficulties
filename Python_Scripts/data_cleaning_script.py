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
import openpyxl
import geopy
from geopy import distance
import statsmodels.formula.api as sm
import plotly.graph_objects as go
from scipy.stats import linregress
import functions_cleaning as fc


np.set_printoptions(threshold=sys.maxsize)


# Paths for accessing files dynamically
sub_path = os.getcwd()
path_cwd = os.path.dirname(sub_path)
path_dta = os.path.join(path_cwd, "Data")
# read in the paths
data = pd.DataFrame(pd.read_csv(path_dta + "/vacancies.csv"))
data = fc.full_dataset_cleaning(dataset=data)
filepath = "/Users/luisenriquekaiser/Desktop/Inhalte/Uni_Bonn/Seminar/Project/Data_cleaned/vacancies_cleaned.csv"
# Check if the folder exists, create it if necessary
if not os.path.exists(os.path.dirname(filepath)):
    os.makedirs(os.path.dirname(filepath))

# Save the data to the file
data.to_csv(filepath)
