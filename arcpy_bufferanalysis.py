# -*- coding: utf-8 -*-
import arcpy
import pandas as pd
import os
import time

# SCRIPT PARAMETERS
bufferDistance = "500 Meters"
timeBin = "3h"
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
wazeOneToManyMatches = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\wazeMatches.shp'
BufferMMDA_shp = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\BufferMMDA.shp'
Buffer_Intersect_shp = 'C:\\Users\\Panji\\Documents\\Python Scripts\\Non-Jupyter Py Scripts\\DOTr\\scratch\\intersection.shp'
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
    arcpy.TableToTable_conversion(fileWaze, scratch, "tableWaze.dbf")
    arcpy.TableToTable_conversion(fileMMDA, scratch, "tableMMDA.dbf")

    # print('Make XY Event Layer')
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

    # Export the shapefile so it can be properly analyzed
    # arcpy.FeatureClassToShapefile_conversion(outputWaze, scratch)
    # arcpy.FeatureClassToShapefile_conversion(outputMMDA, scratch)
    
    # print('Buffer Analysis')
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
    # important, second buffer has NONE dissolve_option
    
    # print('Intersect Analysis')
    arcpy.Intersect_analysis(in_features=[BufferWaze_shp, outputMMDA],
                             out_feature_class=Buffer_Intersect_shp,
                             join_attributes="ALL",
                             cluster_tolerance="",
                             output_type="POINT")

    arcpy.Intersect_analysis(in_features=[BufferMMDA_shp, outputWaze],
                             out_feature_class=Buffer_Intersect_WazeToMMDA,
                             join_attributes="ALL",
                             cluster_tolerance="",
                             output_type="POINT")
    
    
    if runMatchRate == True:
        # Keep track of the matches in a pandas dataframe
        # Get the initial dataframe running
        print('runMatchRate: {}'.format(runMatchRate))
        arcpy.TableToExcel_conversion(Buffer_Intersect_shp, scratchExcel)
        
        if firstLoopMatchRate == True:
            df_match = pd.read_excel(scratchExcel)
            df_match = df_match[0:0]
            firstLoopMatchRate = False
        
        df_selection = pd.read_excel(scratchExcel)
        df_match = df_match.append(df_selection)
        
    if runIntersectionAnalysis == True:
        # Keep track of the Waze data that matches to MMDA data
        # Waze point data inside MMDA buffer
        # Extract time and date to create a unique Excel file
        print('runIntersectionAnalysis: {}'.format(runIntersectionAnalysis))
        
        arcpy.SpatialJoin_analysis(target_features=Buffer_Intersect_WazeToMMDA,
                                   join_features=BufferMMDA_shp,
                                   out_feature_class=wazeOneToManyMatches,
                                   join_operation='JOIN_ONE_TO_ONE',
                                   join_type='KEEP_ALL',
                                   match_option='INTERSECT')

        if firstLoopIntersectionAnalysis == True:

            folder = 'data\\' + 'matches'
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
            
            df_IntersectionAnalysis = pd.DataFrame([row for row in arcpy.da.SearchCursor(wazeOneToManyMatches,field_names='*')])
            firstLoopIntersectionAnalysis = False
            
        fileWazeMatches = fileWaze.split('\\')[-1]
        fileWazeMatches = fileWazeMatches.split('.')[0]
        dataMatchCount = arcpy.GetCount_management(wazeOneToManyMatches)
        dataMatchCount = int(dataMatchCount.getOutput(0))
        dataMatchTotal += dataMatchCount
        if dataMatchCount == 0:
            print('Intersection Analysis: No data')
        else:
            print('Intersection Analysis: {} data, {} total'.format(dataMatchCount, dataMatchTotal))
            df_AppendIntersectionAnalysis = pd.DataFrame([row for row in arcpy.da.SearchCursor(wazeOneToManyMatches,field_names='*')])
            # print(df_AppendIntersectionAnalysis)
            # TRY TO USE CONCAT INSTEAD
            df_IntersectionAnalysis = pd.concat([df_IntersectionAnalysis, df_AppendIntersectionAnalysis])
            arcpy.TableToExcel_conversion(wazeOneToManyMatches, dataMatches + '\\' + fileWazeMatches + '.xls')

    # print('Output Statistics')
    statIntersect = arcpy.GetCount_management(Buffer_Intersect_shp)
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
