#Copyright (c) 2018 Ian Pendleton - MIT License
import os
import time
import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path

from expworkup import googleio

## Set the workflow of the code used to generate the experimental data and to process the data
WorkupVersion=1.0

modlog = logging.getLogger('report.CreateJSON')

def Expdata(DatFile):
    ExpEntry=DatFile
    with open(ExpEntry, "r") as file1:
        file1out=json.load(file1)
        lines=(json.dumps(file1out, indent=4, sort_keys=True))
    lines=lines[:-8]
    return(lines)
    ## File processing for the experimental JSON to convert to the final form (header of the script)

def Robo(robotfile):
    #o the file handling for the robot.xls file and return a JSON object
    robot_dict = pd.read_excel(open(robotfile, 'rb'), header=[0], sheet_name=0)
    reagentlist = []
    for header in robot_dict.columns:
        if 'Reagent' in header and "ul" in header:
            reagentlist.append(header)
    rnum = len(reagentlist)
    robo_df = pd.read_excel(open(robotfile,'rb'), sheet_name=0,usecols=range(0,rnum+2))
    robo_df_2 = pd.read_excel(open(robotfile,'rb'), sheet_name=0,usecols=[rnum+2,rnum+3]).dropna()
    robo_df_3 = pd.read_excel(open(robotfile,'rb'), sheet_name=0,usecols=[rnum+4,rnum+5,rnum+6,rnum+7]).dropna()
    robo_dump=json.dumps(robo_df.values.tolist())
    robo_dump2=json.dumps(robo_df_2.values.tolist())
    robo_dump3=json.dumps(robo_df_3.values.tolist())
    return(robo_dump, robo_dump2, robo_dump3)

def Crys(crysfile):
    ##Gather the crystal datafile information and return JSON object
    headers=crysfile.pop(0)
    crys_df=pd.DataFrame(crysfile, columns=headers)
    crys_df_curated=crys_df[['Concatenated Vial site', 'Crystal Score', 'Bulk Actual Temp (C)', 'modelname']]
    crys_list=crys_df_curated.values.tolist()
    crys_dump=json.dumps(crys_list)
    return(crys_dump)

def genthejson(Outfile, workdir, opfolder, drive_data):
    """Do all of the file handling for a particular run and assemble the JSON, return the completed JSON file object
    and location for sorting and final comparison

    :param Outfile:
    :param workdir:
    :param opfolder:
    :param drive_data:
    :return:
    """
    Crysfile = drive_data
    Expdatafile = workdir + opfolder+'_ExpDataEntry.json'
    Robofile = workdir + opfolder + '_RobotInput.xls'
    exp_return = Expdata(Expdatafile)
    robo_return = Robo(Robofile)
    crys_return = Crys(Crysfile)
    print(exp_return, file=Outfile)
    print('\t},', file=Outfile)
    print('\t', '"well_volumes":', file=Outfile)
    print('\t', robo_return[0], ',', file=Outfile)
    print('\t', '"tray_environment":', file=Outfile)
    print('\t', robo_return[1], ',', file=Outfile)
    print('\t', '"robot_reagent_handling":', file=Outfile)
    print('\t', robo_return[2], ',', file=Outfile)
    print('\t', '"crys_file_data":', file=Outfile)
    print('\t', crys_return, file=Outfile)
    print('}', file=Outfile)

def ExpDirOps(local_directory, debug):
    """Gets all of the relevant folder titles from the experimental directory
    Cross references with the working directory of the final Json files send the list of jobs needing processing

    :param local_directory: The local directory to which to download data. From CLI.
    :param debug: 1 if debug mode, else 0. From CLI.
    :return:
    """
    modlog.info('starting directory parsing')
    if debug == 0:
        # todo this should not be hard coded
        modlog.info('debugging disabled, running on main data directory')
        remote_directory = '13xmOpwh-uCiSeJn8pSktzMlr7BaPDo7B'
    elif debug == 1:
        # todo this also shouldnt be hard coded: put both in a config file
        modlog.warn('debugging enabled! targeting dev folder')
        remote_directory = '1rPNGq69KR7_8Zhr4aPEV6yLtB6V4vx7k'

    crys_dict, robo_dict, Expdata, dir_dict = googleio.drivedatfold(remote_directory)

    # todo: what to do with these log statements? Do we drop this vocabulary
    # modlog.info('parsing EXPERIMENTAL_OBJECT')
    # modlog.info('parsing EXPERIMENTAL_MODEL')
    # modlog.info('parsing REAGENT_MODEL_OBJECT')
    # modlog.info('building runs in local directory')

    print('Building folders ..', end='',flush=True)
    for folder in dir_dict:
        print('.', end='', flush=True)
        exp_json = Path(local_directory + "/%s.json" % folder)
        if exp_json.is_file():
            modlog.info('%s exists' %folder)
        else:
            Outfile=open(exp_json, 'w')
            workdir='data/datafiles/'
            modlog.info('%s Created' %folder)
            data_from_drive = googleio.getalldata(crys_dict[folder],robo_dict[folder],Expdata[folder], workdir, folder)
            genthejson(Outfile, workdir, folder, data_from_drive)
            Outfile.close()
            time.sleep(4)  #see note below
            '''
            due to the limitations of the haverford googleapi 
            we have to throttle the connection a bit to limit the 
            number of api requests anything lower than 2 bugs it out

            This will need to be re-enabled once we open the software beyond
            haverford college until we improve the scope of the googleio api
            '''
    print(' local directories created')
