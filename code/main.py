#!/usr/bin/env python3

#  This file is part of cApps.
#
#  This script is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This script is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cApps.  If not, see <https://www.gnu.org/licenses/>.
#
# Python 3.8.5
# pip 20.0.2
#
# Call script as, e.g.:
# python path/to/code/main.py -l ara-ISR -p path/to/files/ara-ISR
# where path/to/files/ara-ISR is the path to a folder that contains 
# the two unpacked projects, on which the script write_project2excel.groovy
# has been run. 

# ############# AUTHORSHIP INFO ###########################################

__author__ = "Manuel Souto Pico"
__copyright__ = "Copyright 2021, cApps/cApStAn"
__credits__ = ["Manuel Souto Pico"]
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Manuel Souto Pico"
__email__ = "manuel.souto@capstan.be"
__status__ = "Testing" # "Production"


# ############# IMPORTS ###########################################

import sys, time, os, glob
import logging
from pathlib import Path
import pandas as pd
import argparse
import pprint
import hashlib
import requests
#from langtags_client import get_correspondent_tag
import xlsxwriter


# ############# PROGRAM DESCRIPTION ###########################################

text = "This script compares the translation of all segments in common between FT21 and MS22 packages,\
    and will produce a report showing whether the transaltion has changed or not, or if the segment was\
     not found."

# intialize arg parser with a description
parser = argparse.ArgumentParser(description=text)
parser.add_argument("-V", "--version", help="program version", action="store_true")
parser.add_argument("-l", "--locale", help="version/locale name, e.g. 'ara-ISR'")
parser.add_argument("-p", "--path", help="path to version/locale directory, e.g. 'path/to/files/ara-ISR'")

# read arguments from the command line
args = parser.parse_args()

# check for -V or --version
if args.version:
    print(f"This is the workflow creation utility, version {__version__}")
    sys.exit()

if args.locale and args.path:
    locale = args.locale.strip()
    locale_dir_path = Path(args.path.rstrip('/'))
else:
    print("Arguments -l or -p not found.")
    sys.exit()


# ############# LOGGING ###########################################

ts = time.gmtime()
parent_dir = Path(__file__).parent.absolute()
# current working directory (from where the script is called )
#y = Path().absolute()

logdir_path = os.path.join(parent_dir, '_log')
try:
    os.mkdir(logdir_path)
except OSError:
    logging.info("Directory %s was not created, presumably it already existed." % logdir_path)
else:
    logging.info("Successfully created the directory %s " % logdir_path)
formatted_ts = time.strftime("%Y%m%d", ts)
logfile_path = os.path.join(logdir_path, formatted_ts + '.log')

# print(f"The log will be written to '{logfile_path}'")

logging.basicConfig(
    format='[%(asctime)s] %(name)s@%(module)s:%(lineno)d %(levelname)s: %(message)s', 
    filename=logfile_path, 
    level=logging.DEBUG) # encoding='utf-8' only for >= 3.9


# ############# FUNCTIONS ###########################################

# corresponding tag in another convention (taken from langtags_client.py)
def get_correspondent_tag(data, input_tag, source_convention, target_convention):
	return next((tag[target_convention] for tag in data if tag[source_convention] == input_tag), None)


def get_lang_subtag(locale):
    url = 'https://capps.capstan.be/langtags_json.php' ##
    response = requests.get(url)
    data = response.json()
    omt_langtag = get_correspondent_tag(data, 'ara-ISR', 'cApStAn', 'OmegaT')
    return omt_langtag.split('-')[0]


def fstr(template):
    ''' Converts template names that come from the config file into actual strings,
    replacing placeholders between curly brackets with values of previously instantiated values.'''
    return eval(f"f'{template}'")


def get_xls_export_data(path_to_prj, omt_prj_name):
    
    path_to_xls_export = f"{path_to_prj}/{omt_prj_name}/script_output/{omt_prj_name}*.xls"
    logging.info(f"path_to_xls_export: {path_to_xls_export}")
    xls_export = next(file for file in glob.glob(path_to_xls_export)) # to resolve the * 
    #print(f'xls_export: {xls_export}')
    with open(xls_export, 'r') as f:
        data = pd.read_excel(xls_export, sheet_name=None)
    return data


def get_proj_files_from_xls_export(data):
    df = data["Master Sheet"]
    return df.iloc[1:, 0].to_dict()


def define_constants():
    stages = ['2021FT', '2022MS']
    stages_short = ['FT21', 'MS22']
    omt_prj_name_tmpl ="PISA{stage}_{locale}_OMT_Questionnaires"
    target_subtag = get_lang_subtag(locale)
    return [stages, stages_short, omt_prj_name_tmpl, target_subtag]


def create_hash(segment):
    """ Creates hash value of a tuple including segment number and text of the segment. """
    fingerprint = hashlib.md5()
    # fingerprint is a md5 HASH object
    for x in segment:
        fingerprint.update(str(x).encode())
    hash_value = fingerprint.hexdigest()
    #return (hash_value, segment[1])
    return hash_value


# ############# LOGIC ###########################################

if __name__ == '__main__':

    # get constants
    stages, stages_short, omt_prj_name_tmpl, target_subtag = define_constants()

    # build questionnaire dict
    sorted_data = {}
    for stage, stage_short in zip(stages, stages_short):
        
        proj_name = fstr(omt_prj_name_tmpl)
        proj_data = get_xls_export_data(locale_dir_path, proj_name)
        proj_files = get_proj_files_from_xls_export(proj_data)

        for idx, fname in proj_files.items():
            basename = fname.rstrip(f'_{stage_short}_{locale}.xlf')
            if basename not in sorted_data.keys():
                sorted_data.update({basename: {}})

            df = proj_data[str(idx)]
            df.columns = df.iloc[0] # 0 is first row in dataframe excluding the header
            sub_df = df.iloc[1:, 1:4] # rows, cols // get only src, tgt, seg#
            # remove list() and values() below to keep segment numbers (dictionary)
            #xlf_list = list(sub_df.to_dict(orient='index').values())
            xlf_dict = sub_df.to_dict(orient='index')
            
            # create new dict replacing segment numbers with hash values
            hash_dict = {
                create_hash([tu['en'], basename, tu['Segment ID']]): 
                {target_subtag: tu[target_subtag], 'en': tu['en'], 'basename': basename, 'segid': tu['Segment ID']}
                for tu in xlf_dict.values()
                }

            file_data = {stage: hash_dict}
            sorted_data[basename].update(file_data)
            #pprint.pprint(file_data)
    
    #pprint.pprint(sorted_data)

    report = []
    report.append(['file', 'hash', 'segid', 'source', 'target', 'FT version', 'comparison'])
    for filename, questionnaire in sorted_data.items():
        if len(questionnaire) == 2:
            field_trial = questionnaire[stages[0]]
            main_study  = questionnaire[stages[1]]
            for hash_key, segment in main_study.items():
                rpt_row = [filename, hash_key, segment['segid'], segment['en'], segment[target_subtag]]
                if hash_key in field_trial.keys():
                    if segment[target_subtag] == field_trial[hash_key][target_subtag]:
                        rpt_row.append('')
                        rpt_row.append('unaltered')
                    else:
                        rpt_row.append(field_trial[hash_key][target_subtag]) # new translation
                        rpt_row.append('different')
                else:
                    rpt_row.append('')
                    rpt_row.append('not found')
                
                #print(rpt_row)
                report.append(rpt_row)
    

    workbook = xlsxwriter.Workbook(f'pisa_ft2ms_{locale}_transfer_report.xlsx')
    worksheet = workbook.add_worksheet()

    cell_format = workbook.add_format()
    cell_format.set_bold(True)
    #worksheet.set_default_row(20)
    worksheet.set_row(0, 20, cell_format) # row, row height, formatting

    for row_num, row_data in enumerate(report):
        for col_num, col_data in enumerate(row_data):
            worksheet.write(row_num, col_num, col_data)

    workbook.close()
    print(f"Report created successfully for version {locale}")