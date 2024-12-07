import os
import shiny
import shinywidgets
import datetime
import shapely
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import altair as alt
import geopandas as gpd
import seaborn as sns
from shapely.geometry import Point, shape
from shapely import wkt
from termcolor import colored
from shiny import App, render, ui, reactive

# In the second section (def server), update paths!!

app_ui = ui.page_fluid(
     ui.div(
            # Section for the main picture for the DashBoard.
            ui.output_image('main_image'),
            style = "margin-bottom: 0px; padding-bottom: 0px; margin-top: 0px; padding-top: 0px"
        ),
     ui.panel_well(
        # Section I --- Analysis by Community Area
        ui.h1('Section I : Analysis by Community Areas (2015-2024)'), # Found how to do this with Perplexity,
        ui.input_select('admin_unit', 'Choose the community areas to review (Hold Ctrl or Cmd to select multiple) (Applies only to Section I) :',
                        multiple = True,
                        choices = []),
        ui.output_table('table_indicators'),
        ui.layout_sidebar(
            ui.sidebar(
                ui.output_text_verbatim('side_bar_subtitle'),
                ui.output_text_verbatim('number_crime_reported'),
                ui.output_text_verbatim('proportion_arrest'),
                ui.output_image('crime_image'),
                title = f'Distribution of crime counts\nby types per aggregating unit selected'          
            ),
            ui.output_plot('crime_bytype')
        ),
        ui.output_plot('crime_peryear'),
        style = "padding: 0;"            
    ),
    ui.panel_well(
        # Section II Part I --- Mappings crime count by Community Area
        ui.h1('Section II : Mapping of crime counts by Community Area from 2015 to 2024'),
        ui.input_slider(
            'year', 'Choose a year to view a mapping of total crime count by Community Area in Chicago:',
            int(2015), int(2024), int(2015)
        ),
        ui.layout_sidebar(
            ui.sidebar(
                ui.output_image('city_image'),
                ui.output_text_verbatim('create_path_tomap'),
                title = 'Mapping of crime counts\nby Community Area'
            ),
            ui.output_image('map_comm_picture')
        )
    ),
    ui.panel_well(
        # Section II Part II --- Crime count diff (All Communities vs Priority Community Areas)
        ui.input_radio_buttons(
            'vrs_or_not',
            'Choose the communities for which you want to visualize crimes counts before and after VRS implementation',
            choices = ['All Communities', 'Priority Community Areas']
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header('Total crime count before VRS'),
                ui.output_image('map_before_vrs_picture'),
                ui.output_text_verbatim('path_before_vrs')
            ),
            ui.card(
                ui.card_header('Total crime count after VRS'),
                ui.output_image('map_after_vrs_picture'),
                ui.output_text_verbatim('path_after_vrs')
            ),
            ui.card(
                ui.card_header('Difference in crime count before and after VRS'),
                ui.output_image('map_diff_vrs_picture'),
                ui.output_text_verbatim('path_diff_vrs')
            ),
            col_widths = (4, 4, 4)
        )
    ),
    ui.panel_well(
        # Section III - Additional analysis (all communities aggregated)
        ui.h1('Section III : Additional analysis (all Community Areas aggregated)'),
        ui.output_plot('total_crime_peryear'),
        ui.input_slider(
            'year_timing', 'Choose a year the overall timing of crime in Chicago',int(2015),
            int(2024), int(2015)
        ),
        ui.output_image('timing_crime_perday'),
        ui.output_text_verbatim('path_heatmap_timing'),
        ui.output_text_verbatim('space_between_map'),
        ui.output_text_verbatim('warning_message'),
        ui.output_image('comparison_vrs_picture'),
        ui.output_text_verbatim('notice_message_vrs'),
        ui.output_text_verbatim('path_comparison_vrs')
    ),
    ui.panel_well(
        # Section IV - Optional visualization of sample by community areas
        ui.h1('Section IV : Visualization (optional) of data sample by Commmunity Area (2015-2024)'),
        ui.h3('Sample size = 20'),
        ui.input_checkbox(id = "display", label = "View sample data for Community Area", value = False),
        ui.panel_conditional(
            'input.display',
            ui.input_select('community', 'Choose the Community Area you would like to review',
                        choices = []),
            ui.output_table('sample_table_community')
        )
    )
)

def server(input, output, session):
    
    # Setting up all necessary path and objects
    # Update Path
    pictures_path = "C:/Users/Jakub/OneDrive/Documents/GitHub/final_project/pictures" # Update this path to acces the images
    data_base_path = "C:/Users/Jakub/OneDrive/Documents/GitHub/final_project/data" # Update this path to other datasets
    base_path = 'C:/Users/Jakub/Downloads/final_data' # Update this path to acces the large datasets
    # Larger dataset here: 
    # https://drive.google.com/drive/folders/1dFGQ71CesghWY5dWehwiumX57TJQiykV

    vrs_community = ["AUSTIN", "NORTH LAWNDALE", "HUMBOLDT PARK", "WEST GARFIELD PARK",
                     "ENGLEWOOD", "AUBURN GRESHAM", "WEST ENGLEWOOD", "GREATER GRAND CROSSING",
                     "ROSELAND", "EAST GARFIELD PARK", "SOUTH SHORE", "CHICAGO LAWN",
                     "SOUTH LAWNDALE", "CHATHAM", "WEST PULLMAN"]

    # Reading all the data to be used in the next sections
    # Some of those data want be used in the initial dashboard but might
    # be added at later time. 
    @reactive.Calc
    def chicago_communities():
        # Reading the file with the demographic info for 77 communities in Chicago
        chicago_comm = pd.read_csv(f'{data_base_path}/CommAreas_20241127.csv')
        chicago_comm['the_geom'] = chicago_comm['the_geom'].apply(wkt.loads)
        chicago_comm_gdf = gpd.GeoDataFrame(chicago_comm, geometry = 'the_geom', crs = "EPSG:4326")
        return chicago_comm_gdf
    
    @reactive.Calc
    def chicago_district():
        # Reading the file with the demographic info for the districts in Chicago
        chicago_district = pd.read_csv(f'{data_base_path}/PoliceDistrictDec2012.csv')
        chicago_district['the_geom'] = chicago_district['the_geom'].apply(wkt.loads)
        chicago_district_gdf = gpd.GeoDataFrame(chicago_district, geometry = 'the_geom', crs = "EPSG:4326")
        return chicago_district_gdf
    
    @reactive.Calc
    def chicago_ward():
        # Reading the file with the demographic info for the wards in Chicago
        chicago_ward = pd.read_csv(f'{data_base_path}/WARDS_2015.csv')
        chicago_ward['the_geom'] = chicago_ward['the_geom'].apply(wkt.loads)
        chicago_ward_gdf = gpd.GeoDataFrame(chicago_ward, geometry = 'the_geom', crs = "EPSG:4326")
        return chicago_ward_gdf
    
    @reactive.Calc
    def hydepark_crime_data():
        # Reading the file with data on crime in Hyde Park only
        hyde_park_data = pd.read_csv(f'{data_base_path}/Hyde_Park_Crime_20241127.csv')
        return hyde_park_data
    
    @reactive.Calc
    def homicide_crime_data():
        # Reading the file with data on homicides only for Chicago
        homicides_data = pd.read_csv(f'{data_base_path}/Violence_Reduction_-_Victims_of_Homicides_and_Non-Fatal_Shootings_20241125.csv')
        return homicides_data

    @reactive.Calc
    def chicago_crime_data(filetype = 'csv'):
        # Reading the full dataset for the crimes in Chicago from 2015 to 2024 (last upades: 11/27/2024)
        # Function initalized with a kwargs, in case the file type might change later on
        if filetype == 'csv':
            crimes = pd.read_csv(f'{base_path}/Crimes_-_2001_to_Present_20241127.csv')
        else:
            print('Please convert the file to .csv type.')
        crimes['Date'] = pd.to_datetime(crimes['Date'], format = '%m/%d/%Y %I:%M:%S %p')
        crimes['geometry'] = crimes.apply(
            lambda row: Point(row['Longitude'], row['Latitude']),
            axis = 1
        )
        crimes_gdf = gpd.GeoDataFrame(
            crimes,
            geometry = 'geometry',
            crs = "EPSG:4326"
        )
        crimes_gdf = crimes_gdf[(crimes_gdf['Longitude'].between(-87.94011, -87.52413)) &
                                (crimes_gdf['Latitude'].between(41.64454, 42.02304))]
        
        # Joining the full dataset and the dataset with info on communities in Chicago
        chicago_comm_gdf = chicago_communities()
        crimes_comm = gpd.sjoin(
            crimes_gdf, chicago_comm_gdf,
            how = "inner", predicate = "within"
        )
        crimes_comm = crimes_comm.rename(columns = {'index_right' : 'index_community'})
        crimes_comm['COMMUNITY'] = [label.title() for label in crimes_comm['COMMUNITY']]

        # Joining the full dataset and the dataset with info on districts in Chicago
        chicago_dist_gdf = chicago_district()
        crimes_comm_dist = gpd.sjoin(
            crimes_comm, chicago_dist_gdf,
            how = "inner", predicate = "within"
        )
        crimes_comm_dist = crimes_comm_dist.rename(columns = {'index_right' : 'index_district'})
        crimes_comm_dist['DIST_LABEL'] = [label.lower() for label in crimes_comm_dist['DIST_LABEL']]
        # Creating a column for ward name and cleaning it
        crimes_comm_dist['Ward'] = crimes_comm_dist['Ward'].fillna(999)
        crimes_comm_dist['Ward'] = crimes_comm_dist['Ward'].astype(int)
        crimes_comm_dist['Ward_Name'] = crimes_comm_dist['Ward'].apply(
            lambda ward: f'Ward {ward}' if ward != 999 else 'Ward non-assigned'
        )
        return crimes_comm_dist
    
    @reactive.Effect
    def _():
        # To generate the list of community area name to use in the dropdown list
        data = chicago_crime_data()
        list_communities = data['COMMUNITY'].unique()
        list_communities = sorted(list_communities)
        ui.update_select('admin_unit', choices = list_communities)
        
    @reactive.Calc
    def data_filtered_aggregation():
        # Dataset filter by each community area selected as inputs.
        full_data = chicago_crime_data()
        condition = [str(unit) in input.admin_unit() for unit in full_data['COMMUNITY']]
        filtered_data = full_data[condition]
        return filtered_data
    
    
    @render.image  
    def main_image():
        # Uploading the main picture (on top of the dashboard page)
        intro_picture = {
            "src": pictures_path + "/main_picture_dashboard.png",
            "width": "100%",
            "height": "auto"
        }  
        return intro_picture
    
    ########## Section I - Analyzing and comparing main statistics ###########
    #### Plotting by community areas ####
    @reactive.Calc
    def show_district_snippet():
        full_data = chicago_crime_data()
        filtered_data = data_filtered_aggregation()
        table_districts = pd.DataFrame()
        table_districts['Crime Indicators'] = ['Related districts', 'Number of Crimes reported', 'Proportion of Chicago crimes',
                                              'Date most recent crime', 'Date oldest crime',
                                              'Proportion arrest conducted', 'Most frequent type',
                                              'Less frequent type', 'Related ward with most crime', 'Related ward with fewest crime',
                                              'Month with most crime', 'Month with fewest crime',
                                              'Year with most crime', 'Year with fewest crime']
        unique_agg_value = filtered_data['COMMUNITY'].unique()
        all_agg_value = filtered_data['COMMUNITY']
        
        for admin_unit in unique_agg_value:
            second_filter = filtered_data[all_agg_value ==  admin_unit]
            list_indicators = []
            # District name (Indicator 0 = Number of Crimes reported)
            districts_name = '; '.join(list(second_filter['DIST_LABEL'].unique()))
            list_indicators.append(districts_name)

            # Number of crime reported for this district (Indicator 1 = Number of Crimes reported)
            num_reported = len(second_filter)
            list_indicators.append(num_reported)

            # Proportion of crime in chicago (Indicator 2 = Proportion of Chicago crimes)
            prop_crime = round((num_reported / len(full_data)) * 100, 2)
            list_indicators.append(prop_crime)

            # Most recent crimes reported (Indicator 3 = Date most recent crime)
            most_recent = sorted(second_filter['Date'])[-1]
            list_indicators.append(most_recent)

            # Oldest crime reported (Indicator 4 = Date oldest crime)
            oldest = sorted(second_filter['Date'])[0]
            list_indicators.append(oldest)

            # Proportion of arrest for all crimes (Indicator 5 = Proportion arrest conducted)
            num_arrest = len(second_filter[second_filter['Arrest'] == True])
            prop_arrest = round((num_arrest / len(second_filter)) * 100, 2)
            list_indicators.append(prop_arrest)

            # Most frequent type of crime (Indicator 6 = Most frequent type)
            group_typecrime =  second_filter.groupby('Primary Type')
            freq_bytype = group_typecrime.apply(lambda group: len(group))
            freq_bytype = freq_bytype.reset_index()
            freq_bytype.columns = ['type', 'frequency']
            most_frequent_t = freq_bytype['type'][freq_bytype['frequency'] == max(freq_bytype['frequency'])].iloc[0]
            most_frequent_t = most_frequent_t.capitalize()
            list_indicators.append(most_frequent_t)

            # Less frequent type of crime (Indicator 7 = Less frequent type)
            less_frequent_t = freq_bytype['type'][freq_bytype['frequency'] == min(freq_bytype['frequency'])].iloc[0]
            less_frequent_t = less_frequent_t.capitalize()
            list_indicators.append(less_frequent_t)

            # Related ward with the most crime (Indicator 8 = Ward with most crime)
            group_ward =  second_filter.groupby('Ward_Name')
            freq_byward = group_ward.apply(lambda group: len(group))
            freq_byward = freq_byward.reset_index()
            freq_byward.columns = ['Ward_Name', 'frequency']
            most_frequent_w = freq_byward['Ward_Name'][freq_byward['frequency'] == max(freq_byward['frequency'])].iloc[0]
            less_frequent_w = freq_byward['Ward_Name'][freq_byward['frequency'] == min(freq_byward['frequency'])].iloc[0]
            list_indicators.append(most_frequent_w)

            # Related ward with the fewest crime (Indicator 9 = Ward with fewest crime)
            list_indicators.append(less_frequent_w)

            # Month with the most crime (Indicator 12 = Month with most crime)
            second_filter['Month'] = [date.strftime('%B') for date in second_filter['Date']]
            group_month =  second_filter.groupby('Month')
            freq_bymonth = group_month.apply(lambda group: len(group))
            freq_bymonth = freq_bymonth.reset_index()
            freq_bymonth.columns = ['Month', 'frequency']
            most_frequent_m = freq_bymonth['Month'][freq_bymonth['frequency'] == max(freq_bymonth['frequency'])].iloc[0]
            most_frequent_m = most_frequent_m.capitalize()
            list_indicators.append(most_frequent_m)

            # Month with the fewest crime (Indicator 13 = Month with fewest crime)
            less_frequent_m = freq_bymonth['Month'][freq_bymonth['frequency'] == min(freq_bymonth['frequency'])].iloc[0]
            less_frequent_m = less_frequent_m.capitalize()
            list_indicators.append(less_frequent_m)

            # Year with the most crime (Indicator 14 = Year with most crime)
            second_filter['Year'] = [date.year for date in second_filter['Date']]
            group_year =  second_filter.groupby('Year')
            freq_byyear = group_year.apply(lambda group: len(group))
            freq_byyear = freq_byyear.reset_index()
            freq_byyear.columns = ['Year', 'frequency']
            most_frequent_y = freq_byyear['Year'][freq_byyear['frequency'] == max(freq_byyear['frequency'])].iloc[0]
            list_indicators.append(most_frequent_y)

            # Year with the fewest crime (Indicator 15 = Year with fewest crime)
            less_frequent_y = freq_byyear['Year'][freq_byyear['frequency'] == min(freq_byyear['frequency'])].iloc[0]
            list_indicators.append(less_frequent_y)

            # Combining all the indicators
            name_district = str(admin_unit)
            table_districts[name_district] = list_indicators
        return table_districts
    
    @render.table
    def table_indicators():
        table = show_district_snippet()
        return table

    @render.plot
    def crime_peryear():
        filtered_data = data_filtered_aggregation()
        filtered_data['Year'] = [date.year for date in filtered_data['Date']]
        main_group = 'COMMUNITY'
        group_year_unit = filtered_data.groupby([main_group, 'Year'])
        freq_byyearunit = group_year_unit.apply(lambda group: len(group))
        freq_byyearunit = freq_byyearunit.reset_index()
        freq_byyearunit.columns = [main_group, 'Year', 'frequency']

        # Creating the plot now
        fig, ax = plt.subplots()
        for unit in freq_byyearunit[main_group].unique():
            unit_data = freq_byyearunit[freq_byyearunit[main_group] == unit]
            ax.plot(unit_data['Year'], unit_data['frequency'],
                    label = f'{unit}', marker = 'o', markersize = 2)
        ax.set_title(f'Number of reported crimes in all Community Area(s) selected')
        ax.set_xlabel('Year')
        ax.set_ylabel('# of reported crimes')
        ax.legend()
        return fig
    
    @render.plot
    def crime_bytype():
        filtered_data = data_filtered_aggregation()
        main_group = 'COMMUNITY'
        group_typeunit = filtered_data.groupby([main_group, 'Primary Type'])
        freq_bytypeunit = group_typeunit.apply(lambda group: len(group))
        freq_bytypeunit = freq_bytypeunit.reset_index()
        freq_bytypeunit.columns = [main_group, 'Primary Type', 'frequency']
        freq_bytypeunit['Primary Type'] = [type.title() for type in freq_bytypeunit['Primary Type']]
        for index in range(len(freq_bytypeunit)):
            if freq_bytypeunit['Primary Type'].iloc[index] == 'Concealed Carry License Violation':
                freq_bytypeunit['Primary Type'].iloc[index] = 'Concealed License'
            elif freq_bytypeunit['Primary Type'].iloc[index] == 'Interference With Public Officer':
                freq_bytypeunit['Primary Type'].iloc[index] = 'Interference'
            elif freq_bytypeunit['Primary Type'].iloc[index] == 'Offense Involving Children':
                freq_bytypeunit['Primary Type'].iloc[index] = 'Involving Children'
            else:
                pass

        # Plotting
        fig, ax = plt.subplots(figsize = (8, 7))
        for unit in freq_bytypeunit[main_group].unique():
            unit_data = freq_bytypeunit[freq_bytypeunit[main_group] == unit]
            unit_data = unit_data.sort_values(by = 'frequency', ascending = False)
            ax.scatter(
                unit_data['Primary Type'], unit_data['frequency'],
                label = f'{unit}',
                marker = '|',
                linewidth = 4,
                s = 150,
                alpha = 0.8,
                edgecolor = 'black'
            )
        plt.xticks(rotation = 90)
        plt.tight_layout()
        ax.tick_params(axis = 'x', labelsize = 7)
        ax.set_title(
            'Frequency of Crime by Type in selected Community Areas (2015-2024)',
            fontsize = 11,
            pad = 10
        )
        ax.set_xlabel('Types of crime', fontsize = 9, labelpad = 20)
        ax.set_ylabel('# of reported crimes', fontsize = 9)
        ax.legend(fontsize = 12, markerscale = 0.5, handleheight = 1.5)
        plt.subplots_adjust(top = 0.90)
        return fig

    @render.text
    def side_bar_subtitle():
        main_text = f'Community Areas: \n- '
        all_units = '\n- '.join(input.admin_unit())
        warning_text = '\nComparing more than 5\nnot recommended'
        full_text = ''.join([main_text, all_units, warning_text])
        return full_text
    
    @render.text
    def number_crime_reported():
        number = len(data_filtered_aggregation())
        return f'Total_Crime: {number}'
    
    @render.text
    def proportion_arrest():
        data = data_filtered_aggregation()
        data_arrest = data[data['Arrest'] == True]
        prop_arrest = (len(data_arrest) / len (data)) * 100
        return f'% of arrests: {round(prop_arrest, 2)}%'
    
    @render.image  
    def crime_image():
        police_picture = {
            "src": pictures_path + "/crime-scene.png",
            "width": "100%",
            "height": "auto"
        }  
        return police_picture    

    ########## Section II - PART I - Mapping of Crime counts by year #########
    #### Plotting crime count per community area by year ####
    
    @reactive.calc
    def create_mapping_by_comm():
        # Preparing the data
        full_data = chicago_crime_data()
        full_data['Year'] = [date.year for date in full_data['Date']]
        filtered_by_year =  full_data[full_data['Year'] == int(input.year())]
        all_communities = chicago_communities()
        crime_counts = filtered_by_year.groupby(
            "index_community"
        ).size().reset_index(name = "crime_count")
        all_communities = all_communities.reset_index()
        all_communities = all_communities.merge(
            crime_counts, left_index = True, right_on = "index_community", how = "left"
        )
        # Replacing the missing values by 0
        all_communities["crime_count"] = all_communities["crime_count"].fillna(0)

        # Plotting
        fig, ax = plt.subplots(figsize = (20, 7))
        all_communities.plot(
            column = "crime_count",
            cmap = "Reds",
            edgecolor = "black",
            legend = True,
            vmin = 0,
            vmax = 17000,
            ax = ax
        )
        for idx, row in all_communities.iterrows():
            if row["the_geom"].is_empty:
                continue
            centroid = row["the_geom"].centroid
            ax.annotate(
                text = str(row["AREA_NUM_1"]),
                xy = (centroid.x, centroid.y),
                horizontalalignment = "center",
                fontsize = 8,
                color = "black"
            )
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)
        plt.title('Total Crime Count by Community Area in Chicago')

        # Saving the picture to later render it as an image in the shiny app
        map_comm_path = os.path.join(pictures_path, f'{input.year()}_com_crime_total.png')
        plt.savefig(map_comm_path, bbox_inches = 'tight', dpi = 300)
        plt.close()
        return map_comm_path
    
    @render.text
    def create_path_tomap():
        return create_mapping_by_comm()
    
    @render.plot
    def mapping_by_comm():
        map_path = create_path_tomap()
        if map_path and os.path.exists(map_path):
            return plt.imread(map_path)
        else:
            print("Map file not generated or not found")
            return plt.figure() 
    
    @render.image
    def map_comm_picture():
        map_path = os.path.join(pictures_path, f'{input.year()}_com_crime_total.png')
        if os.path.exists(map_path):
            return {"src": map_path, "width": "700px", "height": "auto"}
        else:
            print("Image file not found")
            return None
    
    @render.image  
    def city_image():
        chicago_picture = {
            "src": pictures_path + "/city_chicago.png",
            "width": "100%",
            "height": "auto"
        }  
        return chicago_picture
    
    ########## Section II - PART II - Before and After VRS ############
    #### Mapping of difference between 2015-2019 and 2020-2024 ####
    
    # Plotting before VRS
    @reactive.calc
    def map_before_vrs():
        # Adjusting and filtering to have data before 2020
        full_data = chicago_crime_data()
        full_data['Year'] = [date.year for date in full_data['Date']]
        data_before_vrs = full_data[(full_data['Year'] >= 2018) & (full_data['Year'] <= 2020)]
        all_communities = chicago_communities()
        crime_counts = data_before_vrs.groupby(
            "index_community"
        ).size().reset_index(name = "crime_count")
        all_communities = all_communities.reset_index()
        all_communities = all_communities.merge(
            crime_counts, left_index = True, right_on = "index_community", how = "left"
        )
        # Replacing the missing values by 0
        all_communities["crime_count"] = all_communities["crime_count"].fillna(0)

        # Filtering based on user input
        if input.vrs_or_not() == 'All Communities':
            selected_communities_gdf = all_communities
        elif input.vrs_or_not() == 'Priority Community Areas':
            selected_communities_gdf = all_communities[all_communities["COMMUNITY"].isin(vrs_community)]
        
        # Plotting the map
        fig, ax = plt.subplots(figsize = (20, 7))
        all_communities.plot(
            ax = ax,
            color = 'lightgrey',
            edgecolor='black'
        )
        selected_communities_gdf.plot(
            column = "crime_count",
            cmap = "Reds",
            edgecolor = "black",
            legend = True,
            vmin = 0,
            vmax = 50000,
            ax = ax
        )
        for idx, row in selected_communities_gdf.iterrows():
            if row["the_geom"].is_empty:
                continue
            centroid = row["the_geom"].centroid
            ax.annotate(
                text = str(row["AREA_NUM_1"]),
                xy = (centroid.x, centroid.y),
                horizontalalignment = "center",
                fontsize = 8,
                color = "black"
            )
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)
        plt.title('Total Crime Count by Community Area in Chicago "before" VRS (2018-2020)')

        # Saving the picture to later render it as an image in the shiny app
        map_comm_path = os.path.join(pictures_path, f'{input.vrs_or_not()}_crime_before_vrs.png')
        plt.savefig(map_comm_path, bbox_inches = 'tight', dpi = 300)
        plt.close()
        return map_comm_path
    
    @render.text
    def path_before_vrs():
        return map_before_vrs()
    
    @render.plot
    def mapping_comm_before_vrs():
        map_path = map_before_vrs()
        if map_path and os.path.exists(map_path):
            return plt.imread(map_path)
        else:
            print("Map file not generated or not found")
            return plt.figure() 
    
    @render.image
    def map_before_vrs_picture():
        map_path = os.path.join(pictures_path, f'{input.vrs_or_not()}_crime_before_vrs.png')
        if os.path.exists(map_path):
            return {"src": map_path, "width": "90%", "height": "auto"}
        else:
            print("Image file not found")
            return None
    
    # Plotting map after VRS now
    @reactive.calc
    def map_after_vrs():
        # Adjusting and filtering to have data before 2020
        full_data = chicago_crime_data()
        full_data['Year'] = [date.year for date in full_data['Date']]
        data_after_vrs = full_data[(full_data['Year'] >= 2021) & (full_data['Year'] <= 2023)]
        all_communities = chicago_communities()
        crime_counts = data_after_vrs.groupby(
            "index_community"
        ).size().reset_index(name = "crime_count")
        all_communities = all_communities.reset_index()
        all_communities = all_communities.merge(
            crime_counts, left_index = True, right_on = "index_community", how = "left"
        )
        # Replacing the missing values by 0
        all_communities["crime_count"] = all_communities["crime_count"].fillna(0)

        # Filtering based on user input
        if input.vrs_or_not() == 'All Communities':
            selected_communities_gdf = all_communities
        elif input.vrs_or_not() == 'Priority Community Areas':
            selected_communities_gdf = all_communities[all_communities["COMMUNITY"].isin(vrs_community)]
        
        # Plotting the map
        fig, ax = plt.subplots(figsize = (20, 7))
        all_communities.plot(
            ax = ax,
            color = 'lightgrey',
            edgecolor='black'
        )
        selected_communities_gdf.plot(
            column = "crime_count",
            cmap = "Reds",
            edgecolor = "black",
            legend = True,
            vmin = 0,
            vmax = 50000,
            ax = ax
        )
        for idx, row in selected_communities_gdf.iterrows():
            if row["the_geom"].is_empty:
                continue
            centroid = row["the_geom"].centroid
            ax.annotate(
                text = str(row["AREA_NUM_1"]),
                xy = (centroid.x, centroid.y),
                horizontalalignment = "center",
                fontsize = 8,
                color = "black"
            )
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)
        plt.title('Total Crime Count by Community Area in Chicago "after" VRS (2021-2023)')

        # Saving the picture to later render it as an image in the shiny app
        map_comm_path = os.path.join(pictures_path, f'{input.vrs_or_not()}_crime_after_vrs.png')
        plt.savefig(map_comm_path, bbox_inches = 'tight', dpi = 300)
        plt.close()
        return map_comm_path
    
    @render.text
    def path_after_vrs():
        return map_after_vrs()
    
    @render.plot
    def mapping_comm_after_vrs():
        map_path = map_after_vrs()
        if map_path and os.path.exists(map_path):
            return plt.imread(map_path)
        else:
            print("Map file not generated or not found")
            return plt.figure() 
    
    @render.image
    def map_after_vrs_picture():
        map_path = os.path.join(pictures_path, f'{input.vrs_or_not()}_crime_after_vrs.png')
        if os.path.exists(map_path):
            return {"src": map_path, "width": "90%", "height": "auto"}
        else:
            print("Image file not found")
            return None
    
    # Plotting the difference of crime counts between before and after VRS
    @reactive.calc
    def map_diff_vrs():
        # Finding the difference in crime count
        all_communities = chicago_communities()
        full_data = chicago_crime_data()
        full_data['Year'] = [date.year for date in full_data['Date']]
        # Findind counts before again
        data_before_vrs = full_data[(full_data['Year'] < 2020)]
        crime_counts_before = data_before_vrs.groupby(
            "index_community"
        ).size().reset_index(name = "crime_count")
        all_communities = all_communities.reset_index()
        all_communities_before = all_communities.merge(
            crime_counts_before, left_index = True, right_on = "index_community", how = "left"
        )
        all_communities_before["crime_count"] = all_communities_before["crime_count"].fillna(0)
        # Findind counts after again
        data_after_vrs = full_data[(full_data['Year'] > 2019)]
        crime_counts_after = data_after_vrs.groupby(
            "index_community"
        ).size().reset_index(name = "crime_count")
        all_communities = all_communities.reset_index()
        all_communities_after = all_communities.merge(
            crime_counts_after, left_index = True, right_on = "index_community", how = "left"
        )
        all_communities_after["crime_count"] = all_communities_after["crime_count"].fillna(0)
        # Finding the difference in count now
        crime_count_diff = all_communities_after[['AREA_NUM_1', 'crime_count', 'the_geom']].merge(
            all_communities_before[['AREA_NUM_1', 'crime_count', 'the_geom']], 
            on = 'AREA_NUM_1', 
            suffixes = ('_aftervrs', '_beforevrs')
        )
        crime_count_diff['crime_diff'] = crime_count_diff['crime_count_aftervrs'] - crime_count_diff['crime_count_beforevrs']
        crime_count_diff = crime_count_diff.drop(columns = ['the_geom_beforevrs'])
        crime_count_diff = crime_count_diff.rename(columns = {'the_geom_aftervrs':'the_geom'})

        # Filtering agani based on user input
        if input.vrs_or_not() == 'All Communities':
            crime_count_diff_comm = crime_count_diff
        elif input.vrs_or_not() == 'Priority Community Areas':
            crime_count_diff_comm = crime_count_diff[all_communities["COMMUNITY"].isin(vrs_community)]
        
        # Plotting the map
        fig, ax = plt.subplots(figsize = (20, 7))
        all_communities.plot(
            ax = ax,
            color = 'lightgrey',
            edgecolor='black'
        )
        crime_count_diff_comm.plot(
            column = "crime_diff",
            cmap = "coolwarm",
            edgecolor = "black",
            legend = True,
            vmin = min(crime_count_diff_comm["crime_diff"]),
            vmax = max(crime_count_diff_comm["crime_diff"]),
            ax = ax
        )
        for idx, row in crime_count_diff_comm.iterrows():
            if row["the_geom"].is_empty:
                continue
            centroid = row["the_geom"].centroid
            ax.annotate(
                text = str(row["AREA_NUM_1"]),
                xy = (centroid.x, centroid.y),
                horizontalalignment = "center",
                fontsize = 8,
                color = "black"
            )
        ax.axis("off")
        for spine in ax.spines.values():
            spine.set_visible(False)
        plt.title('Difference in crime Count by Community Area in Chicago before and after VRS')

        # Saving the picture to later render it as an image in the shiny app
        map_comm_path = os.path.join(pictures_path, f'{input.vrs_or_not()}_crime_diff_vrs.png')
        plt.savefig(map_comm_path, bbox_inches = 'tight', dpi = 300)
        plt.close()
        return map_comm_path
    
    @render.text
    def path_diff_vrs():
        return map_diff_vrs()
    
    @render.plot
    def mapping_comm_diff_vrs():
        map_path = map_diff_vrs()
        if map_path and os.path.exists(map_path):
            return plt.imread(map_path)
        else:
            print("Map file not generated or not found")
            return plt.figure() 
    
    @render.image
    def map_diff_vrs_picture():
        map_path = os.path.join(pictures_path, f'{input.vrs_or_not()}_crime_diff_vrs.png')
        if os.path.exists(map_path):
            return {"src": map_path, "width": "90%", "height": "auto"}
        else:
            print("Image file not found")
            return None
    
    ########## Section III - Additional Analysis ############
    #### Analysis for all communities aggregated ####

    @render.text
    def warning_message():
        return 'Important Note: The next plot desaggregates by Priority Community Area'
    
    @render.plot
    def total_crime_peryear():
        # Plotting total crime by year
        full_data = chicago_crime_data()
        full_data['Year'] = [date.year for date in full_data['Date']]
        total_crimes_per_year = full_data.groupby(
            'Year'
        ).size().reset_index(name = 'Total Crimes')
        average_crime_peryear = total_crimes_per_year['Total Crimes'].mean()
        average_crime_peryear = round(average_crime_peryear, 2)

        # Plotting the data
        
        fig, ax = plt.subplots(figsize=(8, 12))
        ax.bar(
            total_crimes_per_year['Year'],
            total_crimes_per_year['Total Crimes'],
            color = 'orange',
            edgecolor = 'black',
            alpha = 0.9,
            width = 0.5
        )
        ax.axhline(
            y = average_crime_peryear,
            color = 'red',
            linestyle = '--',
            linewidth = 1.5,
            label = f'Average crime count per year: {average_crime_peryear}'
        )
        ax.set_ylim(0, 300000)
        ax.set_xlabel('Year', fontsize = 12)
        ax.set_ylabel('Total number of crimes', fontsize = 12)
        ax.set_title('Total Number of Crimes Per Year in all Communities Area(s) (2015-2024)', fontsize = 12)
        ax.set_xticks(total_crimes_per_year['Year'])
        ax.set_xticklabels(total_crimes_per_year['Year'], rotation = 45)
        ax.legend()
        return fig
        
    @reactive.Calc
    def timing_heatmap():
        # Generating the timing heat map based on user input of year
        full_data = chicago_crime_data()
        full_data['Year'] = [date.year for date in full_data['Date']]
        filtered_data = full_data[full_data['Year'] == int(input.year_timing())]
        filtered_data['Weekday'] = filtered_data['Date'].dt.day_name()
        filtered_data['Hour'] = filtered_data['Date'].dt.hour
        # Creating a list of the day for the week to sort the data
        weekday_days = ['Monday', 'Tuesday', 'Wednesday',
                         'Thursday', 'Friday', 'Saturday', 'Sunday']
    
        # Set the 'Weekday' column to be categorical with a specific order
        filtered_data['Weekday'] = pd.Categorical(
            filtered_data['Weekday'],
            categories = weekday_days,
            ordered = True
        )
    
        timing_analysis = filtered_data.groupby(
            ['Weekday', 'Hour']
        ).size().reset_index(name = 'Count')
        timing_analysis_pivoted = timing_analysis.pivot_table(
            index = 'Weekday',
            columns = 'Hour',
            values = 'Count',
            aggfunc = 'sum',
            fill_value = 0
        )

        # Plotting the heat map
        plt.figure(figsize = (40, 9))
        sns.heatmap(
            timing_analysis_pivoted,
            cmap = 'YlGnBu',
            annot = False,
            cbar_kws = {'label': 'Crime Count'},
            vmin = 0,
            vmax = 3000
        )
        plt.title(
            'Timing of crime frequency by weekday',
            fontsize = 30,
            pad = 20
        )
        plt.xlabel('Hour of the Day', fontsize = 17)
        plt.ylabel('Day of the Week', fontsize = 17)
        plt.xticks(fontsize = 14)
        plt.yticks(fontsize = 12)
        plt.legend(fontsize = 30)
        plt.tight_layout()

        # Saving the picture to later render it as an image in the shiny app
        map_comm_path = os.path.join(pictures_path, f'{input.year_timing()}_heatmap_timing_crime.png')
        plt.savefig(map_comm_path, bbox_inches = 'tight', dpi = 600)
        plt.close()
        return map_comm_path
    
    @render.text
    def path_heatmap_timing():
        return timing_heatmap()
    
    @render.plot
    def heatmap_timing_plot():
        map_path = timing_heatmap()
        if map_path and os.path.exists(map_path):
            return plt.imread(map_path)
        else:
            print("Map file not generated or not found")
            return plt.figure() 
    
    @render.image
    def timing_crime_perday():
        map_path = os.path.join(pictures_path, f'{input.year_timing()}_heatmap_timing_crime.png')
        if os.path.exists(map_path):
            return {"src": map_path, "width": "1600px", "height": "auto"}
        else:
            print("Image file not found")
            return None
    
    @render.text
    def space_between_map():
        return '  '
    
    @reactive.Calc
    def generate_vrs_vs_after():
        # Plotting to compare the period VRS implementation (2018-2020) and
        # the years after this period in the targeted communities.
        full_data = homicide_crime_data()
        filtered_data = full_data[full_data['COMMUNITY_AREA'].isin(vrs_community)]
        filtered_data['DATE'] = pd.to_datetime(filtered_data['DATE'], format = '%m/%d/%Y %I:%M:%S %p')
        filtered_data['Year'] = filtered_data['DATE'].dt.year
        filtered_data['Period'] = filtered_data['Year'].apply(
            lambda year: '2018–2020' if 2018 <= year <= 2020 else '2021–2023' if 2021 <= year <= 2023 else None
        )
        filtered_data = filtered_data[filtered_data['Period'].notna()]
        summary_all = filtered_data.groupby(
            ['COMMUNITY_AREA', 'Period']
        ).size().reset_index(name = 'Count')
        summary_all['COMMUNITY_AREA'] = [comm.title() for comm in summary_all['COMMUNITY_AREA']]
        vrs_community_title = [vrs.title() for vrs in vrs_community]

        # Pivot the summary dataframe to make plotting easier
        summary_all_pivoted = summary_all.pivot(
            index = 'COMMUNITY_AREA',
            columns = 'Period',
            values = 'Count'
        ).fillna(0)

        # Plotting
        fig, ax = plt.subplots(figsize=(30, 7))
        summary_all_pivoted.plot(
            kind = 'bar',
            ax = ax,
            color = ['#1f77b4', '#ff7f0e'],
            width = 0.7
        )
        ax.set_title(
            'Homicides and Non-Fatal Shootings Across Priority Community Areas (2018–2020 vs. 2021–2023)',
            fontsize = 23
        )
        ax.set_xlabel('Community Areas', fontsize = 14)
        ax.set_ylabel('Number of Incidents', fontsize = 14)
        ax.set_xticklabels(
            summary_all_pivoted.index,
            rotation = 90,
            ha = 'right',
            fontsize = 14
        )
        ax.legend(
            title = 'Period',
            fontsize = 14,
            labels = ['2018–2020', '2021–2023']
        )
        plt.tight_layout()

        # Saving the picture to later render it as an image in the shiny app
        map_comm_path = os.path.join(pictures_path, 'homicide_beforeafter_vrs.png')
        plt.savefig(map_comm_path, bbox_inches = 'tight', dpi = 600)
        plt.close()
        return map_comm_path
    
    @render.text
    def path_comparison_vrs():
        return generate_vrs_vs_after()
    
    @render.plot
    def graph_comparison_vrs():
        map_path = generate_vrs_vs_after()
        if map_path and os.path.exists(map_path):
            return plt.imread(map_path)
        else:
            print("Map file not generated or not found")
            return plt.figure() 
    
    @render.image
    def comparison_vrs_picture():
        map_path = os.path.join(pictures_path, 'homicide_beforeafter_vrs.png')
        if os.path.exists(map_path):
            return {"src": map_path, "width": "1650px", "height": "auto"}
        else:
            print("Image file not found")
            return None
    
    @render.text
    def notice_message_vrs():
        message = 'VRS was implemented accross all community areas of Chicago, targeting more precisely 15 community areas most affected by violence over the period 2018-2020.'
        return message

    ########## Section IV - Data Sample by Community Area ############
    #### Viewing (optional) table sample by Community Area ####
        
    @reactive.Effect
    def _():
        # Generating the list of community area again to avoid wrong calling
        data = chicago_crime_data()
        community_variable = data['COMMUNITY']
        community_variable = community_variable.fillna('Non-assigned Community')
        community_variable = community_variable.unique()
        community_variable = sorted(community_variable)
        ui.update_select('community', choices = community_variable)

    @reactive.Calc
    def data_filtered_community():
        # Filtering again to avoid calling previous data that were already manipulated
        full_data = chicago_crime_data()
        full_data['COMMUNITY'] = full_data['COMMUNITY'].fillna('Non-assigned Community')
        condition = [community == input.community() for community in full_data['COMMUNITY']]
        filtered_data = full_data[condition]
        return filtered_data
    
    @render.table
    def sample_table_community():
        # Generating the sample table
        data = data_filtered_community()
        data_selected = data[['Date', 'Primary Type', 'DIST_LABEL',
                              'Ward_Name', 'Location Description',
                              'Arrest']]
        data_selected['Primary Type'] = [type.title() for type in data_selected['Primary Type']]
        data_selected['Location Description'] = data_selected['Location Description'].fillna('No Description')
        data_selected['Location Description'] = [location.title() for location in data_selected['Location Description']]
        return data_selected.sample(n = 20)

app = App(app_ui, server)