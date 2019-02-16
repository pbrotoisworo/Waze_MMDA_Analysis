# -*- coding: utf-8 -*-
import arcpy
import pandas as pd
import os
import time

# SCRIPT PARAMETERS
bufferDistance = "500 Meters" # This is radius and not diameter of the circle
timeBin = "3h" # Only used for file naming purposes
runMatchRate = True
runIntersectionAnalysis = True

# Declare initial variables
scratch = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch'
scratchExcel = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\scratchCsv.xls'
df = pd.read_csv('combined_table.csv')
spRef = arcpy.SpatialReference("C:\\GIS\\Data Files\\Work Files\\MMDA Tweet2Map\\input\\GCS_WGS_1984.prj")
outputWaze = 'outputWaze'
outputWazeFile = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\' + outputWaze + '.shp'
outputMMDA = 'outputMMDA'
outputMMDAFile = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\' + outputMMDA + '.shp'
BufferWaze_shp = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\BufferWaze.shp'
WazeToMMDAMatches = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\wazeMatches.shp'
BufferMMDA_shp = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\BufferMMDA.shp'
Buffer_Intersect_MMDAToWaze = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\intersection.shp'
Buffer_Intersect_WazeToMMDA = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\intersection_WazeToMMDA.shp'
dataMatches = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\data\\matches'
dataMatchTotal = 0
wazeTotal = 0
MMDATotal = 0
MMDADuplicateTotal = 0
duplicateTotal = 0
firstLoopMatchRate = True
firstLoopIntersectionAnalysis = True

# Process: Set workspace environment
print('Set workspace environment')
arcpy.env.workspace = r'C:\Users\Panji\Documents\Python Scripts\Non-Jupyter Py Scripts\DOTr\scratch'
print('Set output coordinate system')
arcpy.env.outputCoordinateSystem = spRef
arcpy.env.overwriteOutput = True

for idxMMDA, csvMMDA in enumerate(df['MMDA']):

    print('===============================================')

    # Get file from both MMDA and Waze
    for idxWaze, csvWaze in enumerate(df['Waze']):

        if (idxMMDA == idxWaze) and '.txt' not in csvWaze:
            fileMMDA = csvMMDA
            fileWaze = csvWaze
            break
        
    print('Waze: ' + fileWaze)
    print('MMDA: ' + fileMMDA)
    
    # print('Table to Table')
    # Convert the CSV file into a .dbf format so ArcMap can read it
    arcpy.TableToTable_conversion(fileWaze, scratch, "tableWaze.dbf")
    arcpy.TableToTable_conversion(fileMMDA, scratch, "tableMMDA.dbf")

    # print('Make XY Event Layer')
    # Make a temporary point layer from the .dbf file
    # The EXCEPT code catches empty dataset and then skips to the next loop
    try:
        arcpy.MakeXYEventLayer_management(table=scratch + '\\tableMMDA.dbf',
                                          in_x_field="longitude",
                                          in_y_field="latitude",
                                          out_layer=outputMMDA,
                                          spatial_reference=spRef)
        arcpy.MakeXYEventLayer_management(table=scratch + '\\tableWaze.dbf',
                                          in_x_field="longitude",
                                          in_y_field="latitude",
                                          out_layer=outputWaze,
                                          spatial_reference=spRef)
    except:
        print('No data detected. Skipping set')
        continue

    # Export the shapefile so it can be analyzed (No need anymore)
    # arcpy.FeatureClassToShapefile_conversion(outputWaze, scratch)
    # arcpy.FeatureClassToShapefile_conversion(outputMMDA, scratch)
    
    # print('Buffer Analysis')
    # important, second buffer (MMDA) has NONE dissolve_option
    # this is because we are testing Waze data against every unique MMDA point
    # The Waze buffers are joined together because the main script tests
    # if MMDA (or any other dataset) falls within the Waze dataset and DOES NOT
    # track anything else. Check 'runMatchRate' and 'runIntersectionAnalysis'
    # for more analysis options.
    arcpy.Buffer_analysis(in_features=outputWaze,
                          out_feature_class=BufferWaze_shp,
                          buffer_distance_or_field=bufferDistance,
                          line_side="FULL",
                          line_end_type="ROUND",
                          dissolve_option="ALL",
                          method="PLANAR")
    arcpy.Buffer_analysis(in_features=outputMMDA,
                          out_feature_class=BufferMMDA_shp,
                          buffer_distance_or_field=bufferDistance,
                          line_side="FULL",
                          line_end_type="ROUND",
                          dissolve_option="NONE",
                          method="PLANAR")
    
    
    # print('Intersect Analysis')
    # The first intersection analysis is MMDA point data that intersects
    # with the Waze Buffer
    # The second is Waze data that intersects with the MMDA buffer
    arcpy.Intersect_analysis(in_features=[BufferWaze_shp, outputMMDA],
                             out_feature_class=Buffer_Intersect_MMDAToWaze,
                             join_attributes="ALL",
                             cluster_tolerance="",
                             output_type="POINT")

    arcpy.Intersect_analysis(in_features=[BufferMMDA_shp, outputWaze],
                             out_feature_class=Buffer_Intersect_WazeToMMDA,
                             join_attributes="ALL",
                             cluster_tolerance="",
                             output_type="POINT")
    
    
    if runMatchRate == True:
        # This module saves the matching data points and creates them in a new
        # Excel file. This module saves the MMDA (or other data being compared)
        # that intersects the Waze data. The purpose of this module is so you
        # can analyze the matching data points.

        
        print('runMatchRate: {}'.format(runMatchRate))
        arcpy.TableToExcel_conversion(Buffer_Intersect_MMDAToWaze, scratchExcel)
        
        if firstLoopMatchRate == True:
            # Get the initial dataframe running
            df_match = pd.read_excel(scratchExcel)
            df_match = df_match[0:0]
            firstLoopMatchRate = False
        
        df_selection = pd.read_excel(scratchExcel)
        df_match = df_match.append(df_selection)
        
    if runIntersectionAnalysis == True:
        # This is the OPPOSITE of the main script. While the main script looks
        # at the MMDA points compared to Waze. This module looks at Waze versus
        # the MMDA points and then attaches the intersecting MMDA data to the
        # Waze point.
        # Extract time and date to create a unique Excel file
        print('runIntersectionAnalysis: {}'.format(runIntersectionAnalysis))

        # Target for spatial join is the point data from Waze that intersects MMDA
        # match_option is INTERSECT. Thus, if target feature is intersecting
        # the join_feature MMDA BUFFER. Then the attributes of the MMDA buffer
        # that it is intersecting with will be joined to the Waze data point.
        #
        # A ONE_TO_ONE operation is chosen because we are looking at whether or not
        # Waze data intersects a data point. If a MANY_TO_ONE operation is chosen
        # The target feature will be duplicated if it is inside multiple buffers,
        # leading to an overinflation of Waze points.
        arcpy.SpatialJoin_analysis(target_features=Buffer_Intersect_WazeToMMDA,
                                   join_features=BufferMMDA_shp,
                                   out_feature_class=WazeToMMDAMatches,
                                   join_operation='JOIN_ONE_TO_ONE',
                                   join_type='KEEP_ALL',
                                   match_option='INTERSECT')

        if firstLoopIntersectionAnalysis == True:
            # first loop to create the initial dataframe

            folder = 'data\\' + 'matches'
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
            
            df_IntersectionAnalysis = pd.DataFrame([row for row in arcpy.da.SearchCursor(WazeToMMDAMatches,field_names='*')])
            firstLoopIntersectionAnalysis = False
            
        fileWazeMatches = fileWaze.split('\\')[-1]
        fileWazeMatches = fileWazeMatches.split('.')[0]
        dataMatchCount = arcpy.GetCount_management(WazeToMMDAMatches)
        dataMatchCount = int(dataMatchCount.getOutput(0))
        dataMatchTotal += dataMatchCount
        if dataMatchCount == 0:
            print('Intersection Analysis: No data')
        else:
            print('Intersection Analysis: {} data, {} total'.format(dataMatchCount, dataMatchTotal))
            df_AppendIntersectionAnalysis = pd.DataFrame([row for row in arcpy.da.SearchCursor(WazeToMMDAMatches,field_names='*')])
            # print(df_AppendIntersectionAnalysis)
            # TRY TO USE CONCAT INSTEAD
            # In every loop the new data will be appended to the main data by
            # using pd.concat
            df_IntersectionAnalysis = pd.concat([df_IntersectionAnalysis, df_AppendIntersectionAnalysis])
            # arcpy.TableToExcel_conversion(WazeToMMDAMatches, dataMatches + '\\' + fileWazeMatches + '.xls')

    # print('Output Statistics')
    # Get total count of MMDA data that intersects with Waze
    statIntersect = arcpy.GetCount_management(Buffer_Intersect_MMDAToWaze)
    statIntersect = int(statIntersect.getOutput(0))
    statWaze = arcpy.GetCount_management(outputWaze)
    statWaze = int(statWaze.getOutput(0))
    statMMDA = arcpy.GetCount_management(outputMMDA)
    statMMDA = int(statMMDA.getOutput(0))

    # Clean outputs
    # print('Reset variables')
    arcpy.Delete_management("in_memory")
    arcpy.Delete_management('C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\tableWaze.dbf')
    arcpy.Delete_management('C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\tableMMDA.dbf')
    arcpy.Delete_management(outputMMDAFile)
    arcpy.Delete_management(outputWazeFile)

    # Statistics
    wazeTotal += statWaze
    MMDATotal += statMMDA
    duplicateTotal += statIntersect
    duplicateRatio = float(float(duplicateTotal) / float(MMDATotal))
    
    print('\nCURRENT SET:')
    print('Waze Incidents: {}'.format(statWaze))
    print('MMDA Incidents: {}'.format(statMMDA))
    print('Total duplicates: {}\n\n'.format(statIntersect))
    print('TOTAL SET:')
    print('Total Waze Incidents: {}'.format(wazeTotal))
    print('Total MMDA Incidents: {}'.format(MMDATotal))
    print('Total MMDA Duplicates: {}'.format(duplicateTotal))
    print('Duplicate/MMDA Total: {}/{}\n'.format(duplicateTotal, MMDATotal))
    print('Current MMDA Duplicate Ratio: {:.2f}'.format(duplicateRatio))

# Save CSV files from the extra modules
if runMatchRate == True:
    df_match.to_csv(r'C:\Users\Panji\Documents\Python Scripts\Non-Jupyter Py Scripts\DOTr\data\Contribution of Waze\histogram_{}_{}.csv'.format(timeBin, bufferDistance),
                    index=False, encoding='utf-8')
    print('Current matching dataframe shape: {}'.format(df_match.shape))
if runIntersectionAnalysis == True:
    df_IntersectionAnalysis.to_csv(r'C:\Users\Panji\Documents\Python Scripts\Non-Jupyter Py Scripts\DOTr\data\Contribution of Waze\IntersectionAnalysis_{}_{}.csv'.format(timeBin, bufferDistance),
                                   encoding='utf-8')
    
print('===============================')
print('\nAnalysis done!')
print('Duplicate/MMDA Total: {}/{}'.format(duplicateTotal, MMDATotal))
print('Current MMDA Duplicate Ratio: {:.2f}\n'.format(duplicateRatio))
