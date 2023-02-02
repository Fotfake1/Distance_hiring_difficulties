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


def __fill_in_gps_coordinates(df1, column1, df2, column2):
    """
    df1: the Pandas dataframe cont  aining the column to be updated
    column1: the name of the column in df1 to be looped through
    df2: the Pandas dataframe containing the column to search for matching values
    column2: the name of the column in df2 to search for matching values
    update_column: the name of the column in df1 to update with values from df2
    """
    # initialize the longitudinal and the latidudinal columns
    df1["Latitudal_coordinates_organization"] = -1
    df1["Longitudinal_coordinates_organization"] = -1
    df1["Fuzzy_Rating"] = -1
    for index, row in df1.iterrows():
        value = row[column1]
        matches = df2[df2[column2] == value]
        if not matches.empty:
            df1.at[index, "Latitudal_coordinates_organization"] = matches.iloc[0][
                "Latitudal_coordinates_organization"
            ]
            df1.at[index, "Longitudinal_coordinates_organization"] = matches.iloc[0][
                "Longitudinal_coordinates_organization"
            ]
            df1.at[index, "Fuzzy_Rating"] = matches.iloc[0]["fuzzy_rating"]
    return df1


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


def __harmonize_strings(df, column_name):
    """
    This function harmonizes the strings of the column given to it,
    to the general naming conventions. This function does:
        - removal of trailing spaces
        - removal of multiple splces
        - removal of umlauts
        - make everything lowercase
        - removes rows with na
    Input: df(Pd.Datafr)
    """
    # remove trailing or leading spaces
    series = df[str(column_name)]
    df[column_name] = series.str.strip()
    # making the string lowercase
    df[column_name] = df[column_name].str.lower()
    # replace ÄÖÜß with ae,oe,ue, ss
    dictOfStrings = {
        "Ä": "Ae",
        "ä": "ae",
        "Ö": "Oe",
        "ö": "oe",
        "Ü": "ue",
        "ü": "ue",
        "ß": "ss",
    }
    for word, replacement in dictOfStrings.items():
        df[column_name] = df[column_name].replace(word, replacement)
    df = df[df[column_name].notna()]
    return df


def __find_gps_coordinates(df, gps_df, column_name_df, column_name_gps):
    """
    This function should find the city in Germany,
    given to the function in a spreadshet with gps coordinates. - it works with substrings as well.
    The function is based on a fuzyy searching algorithm, which works with a special distance measure
    between strings.
    Input:  - df(pd.df): The dataframe with the city names
            - gps_df : The dataframe with all german cities and their respective names
            - column_name_df(string): The name of the column with the city names
            - column_name_gps: The name of the column with the gps data
    Output:  - df: A dataframe with two new columns indicating the longitudinal and the latitudinal position of the cities
    Raises: None
    """
    # initialize the longitudinal and the latidudinal columns
    df["Latitudal_coordinates_organization"] = -1
    df["Longitudinal_coordinates_organization"] = -1
    df["best_match_name"] = "Nothing"
    df["fuzzy_rating"] = 0
    # loop through all elements in the column with the city names
    for i, name_df in enumerate(df[column_name_df]):
        # check, if the city name is in the list of german city names
        # initialize the highest fuzz ratio and the index of the highest fuzz ratio
        index_highest_fuzzy_ratio = -1
        highest_fuzz = 0
        # loop through the column with all the city names
        for j, name_gps in enumerate(gps_df[column_name_gps]):
            ratio = fuzz.ratio(str(name_df), str(name_gps))
            if ratio > highest_fuzz:
                highest_fuzz = ratio
                index_highest_fuzzy_ratio = j
            # for the highest fuzz index, get the gps coordinates

        if index_highest_fuzzy_ratio != -1:
            df.loc[i, "Latitudal_coordinates_organization"] = gps_df.loc[
                index_highest_fuzzy_ratio, "Breitengrad"
            ]
            df.loc[i, "Longitudinal_coordinates_organization"] = gps_df.loc[
                index_highest_fuzzy_ratio, "Längengrad"
            ]
            df.loc[i, "best_match_name"] = gps_df.loc[
                index_highest_fuzzy_ratio, column_name_gps
            ]
            df.loc[i, "fuzzy_rating"] = highest_fuzz

    return df


def __find_best_match(df1, df2, col1, col2):
    # create a dictionary to store the best match for each element in df1[col1]
    best_matches = {}

    # loop through all the elements in df1[col1]
    for element in df1[col1]:
        # initialize the highest fuzz ratio and the best match
        highest_fuzz = 0
        best_match = None

        # loop through all the elements in df2[col2]
        for candidate in df2[col2]:
            # calculate the fuzz ratio between the current element and candidate
            ratio = fuzz.ratio(element, candidate)

            # if the current candidate has a higher fuzz ratio than the current highest_fuzz,
            # update the highest_fuzz and the best_match
            if ratio > highest_fuzz:
                highest_fuzz = ratio
                best_match = candidate

        # add the best match for the current element to the best_matches dictionary
        best_matches[element] = best_match

    # return the dictionary of best matches
    return best_matches


def __drop_not_used_columns(data, used_columns):
    all_columns = data.columns
    delta = [col for col in all_columns if col not in used_columns]
    data = data.drop(columns=delta, inplace=False)
    # data = data.drop(columns=[col for col in data.columns if col not in used_columns], inplace=True)
    return data


def create_distance_measures(data, city_gps_match_data, used_columns):
    ###### harmonizing the organization location name.
    data = __harmonize_strings(df=data, column_name="organization_location_name")

    ## hamonize the strings of the gps - city name spreadsheet
    city_gps_match_data = __harmonize_strings(
        df=city_gps_match_data, column_name="Stadt"
    )
    data = __delete_rows_with_unique_values(
        dataframe=data, column_name="organization_location_name"
    )
    data = data.dropna(subset=["location_coordinates"])
    # create a dataframe with city names without duplicates, which is easier to loop over later
    city_names = pd.DataFrame(
        {"organization_location_name": data["organization_location_name"].unique()}
    )
    ## find the gps coordinates for all the unique city names
    city_names = __find_gps_coordinates(
        df=city_names,
        gps_df=city_gps_match_data,
        column_name_df="organization_location_name",
        column_name_gps="Stadt",
    )
    city_names.to_excel("city_names_match.xlsx")

    ## map the gps coordinates back
    data = __fill_in_gps_coordinates(
        df1=data,
        df2=city_names,
        column1="organization_location_name",
        column2="organization_location_name",
    )

    # Only consider those rows, with a fuzzy rating above 85, since these I expect to b emapped rightly.
    data = data[data["Fuzzy_Rating"] >= 85]
    data["latitudal_coordinates_job"] = pd.to_numeric(
        data["location_coordinates"].str.split(",", expand=True)[0]
    )
    data["longitudinal_coordinates_job"] = pd.to_numeric(
        data["location_coordinates"].str.split(",", expand=True)[1]
    )
    data["distance_between_job_and_organization"] = -1
    for i in range(len(data)):
        cords1 = (
            data["latitudal_coordinates_job"].iloc[i],
            data["longitudinal_coordinates_job"].iloc[i],
        )
        cords2 = (
            data["Latitudal_coordinates_organization"].iloc[i],
            data["Longitudinal_coordinates_organization"].iloc[i],
        )
        data["distance_between_job_and_organization"].iloc[i] = geopy.distance.geodesic(
            cords1, cords2
        ).km

    data = __drop_not_used_columns(data=data, used_columns=used_columns)
    return [data, city_names]
