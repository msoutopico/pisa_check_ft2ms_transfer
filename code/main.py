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

# pipenv install --python 3.9.1
# call it from cron as: every 5 min, pipenv run python3 mk_workflows.py -i /path/to/init/bundle -c /path/to/config/file -m /path/to/mapping/file (memoq_capstan_mapping_20210512.xlsx)


# ############# AUTHORSHIP INFO ###########################################

__author__ = "Manuel Souto Pico"
__copyright__ = "Copyright 2021, cApps/cApStAn"
__credits__ = ["Manuel Souto Pico"]
__license__ = "GPL"
__version__ = "0.1.0"
__maintainer__ = "Manuel Souto Pico"
__email__ = "manuel.souto@capstan.be"
__status__ = "Testing / pre-production" # "Production"


# ############# IMPORTS ###########################################

import sys, time, os, glob
import logging
from pathlib import Path
import pandas as pd
import argparse
import pprint


# ############# PROGRAM DESCRIPTION ###########################################

text = "This application automates the creation of workflow folders and creates OmegaT project packages"

# intialize arg parser with a description
parser = argparse.ArgumentParser(description=text)
parser.add_argument("-V", "--version", help="show program version", action="store_true")
parser.add_argument("-l", "--locale", help="version name")
parser.add_argument("-p", "--path", help="path to version/locale directory")
#parser.add_argument("-o", "--origin", help="path to the file with the original translation (e.g. FT21)")
#parser.add_argument("-e", "--edited", help="path to the file with the edited translation (e.g. MS22)")
# parser.add_argument("-c", "--config", help="specify path to config file")

# read arguments from the command line
args = parser.parse_args()

# check for -V or --version
if args.version:
    print(f"This is the workflow creation utility, version {__version__}")
    sys.exit()


#if args.origin and args.edited:
#    origin = Path(args.origin.rstrip('/'))
#    edited = Path(args.edited.rstrip('/'))
if args.locale and args.path:
    locale = args.locale.strip()
    locale_dir_path = Path(args.path.rstrip('/'))
else:
    print("Arguments -l or -p not found.")
    sys.exit()



# ############# LOGGING ###########################################

ts = time.gmtime()
# the directory of this script being run (e.g. /path/to/cli_automation/flash_prepp_help)
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
#open(log_fname, "a")
print(f"The log will be written to '{logfile_path}'")

logging.basicConfig(
    format='[%(asctime)s] %(name)s@%(module)s:%(lineno)d %(levelname)s: %(message)s', 
    filename=logfile_path, 
    level=logging.DEBUG) # encoding='utf-8' only for >= 3.9


# ############# FUNCTIONS ###########################################


def fstr(template):
    ''' Converts template names that come from the config file into actual strings,
    replacing placeholders between curly brackets with values of previously instantiated values.'''
    return eval(f"f'{template}'")


def get_xls_export_data(path_to_prj, omt_prj_name):
    
    path_to_xls_export = f"{path_to_prj}/{omt_prj_name}/script_output/{omt_prj_name}*.xls"
    logging.info(f"path_to_xls_export: {path_to_xls_export}")
    xls_export = next(file for file in glob.glob(path_to_xls_export)) # to resolve the * 
    print(f'xls_export: {xls_export}')
    with open(xls_export, 'r') as f:
        data = pd.read_excel(xls_export, sheet_name=None)
    return data


def get_langtag_from_fname(src_file, langtags):
    if any(tag in src_file for tag in langtags):
        tags = [tag for tag in langtags if(tag in src_file)]
        return max(tags, key=len)  # returning the longest code found (dut-NL, not dut)
    else:
        return None


def get_proj_files_from_xls_export(data):
    df = data["Master Sheet"]
    return df.iloc[1:, 0].to_dict()


def define_constants():
    stages = ['2021FT', '2022MS']
    stages_short = ['FT21', 'MS22']
    omt_prj_name_tmpl ="PISA{stage}_{locale}_OMT_Questionnaires"
    return [stages, stages_short, omt_prj_name_tmpl]


def get_data_from_xlf(path_to_dir, omt_prj_name, target_lang):

    list_of_dfs = []

    logging.info(f"Traverse proj_files")
    for idx, fname in proj_files.items():
        if target_lang == None:
            logging.warning(f"Language tag for the text to send to MT not defined")
            return False # send to translate

        logging.info(f"target_lang: {target_lang}")
        # data comes from the omt export in excel (passive)
        df = data[str(idx)]
        df.columns = df.iloc[0] # 0 is first row in dataframe excluding the header
        #df.iloc[0, 0] = "Seg #"
        sub_df = df.iloc[1:, 0:3] # rows, cols // get only seg#, src, tgt
        try:
            s = sub_df[target_lang.split('-')[0]] # series
            logging.info(f"Getting series successful")
            logging.info(s)
        except:
            logging.error(f"Exception while trying to get series for language {target_lang}")
            return False

        if isinstance(s, pd.DataFrame):
            # this happens when src and tgt are both 'en', clean_strings expects a series, not a df
            logging.warning(f"s is a dataframe, likely source and target languages are the same")
            logging.info(s.iloc[ :, 1])
            logging.info("Getting only the second series/column in the df")
            s = s.iloc[ :, 1]
        elif isinstance(s, pd.Series):
            logging.info(f"s is already a series, fine") 


        clean_list = clean_strings(s.tolist())
        #logging.info(f"clean_list: {clean_list}")

        logging.info(f">>> target_lang: {target_lang}")
        logging.info(f"Sending {target_lang} strings in '{fname}' to {mt_engine}")
        mt = get_mt_of_list(clean_list, target_lang, "en")
        #mt = ["The 3 promotional messages shown are to invite you to participate in the conference on Europe's future.", 'Is this purpose clear to you for each of these messages?', '{@}', 'Yes, definitely', 'Yes, to some extent', 'No, not really', 'No not at all', 'Do not know', 'Below we show some promotional messages that can be used to communicate about the conference on the future of Europe.', "The conference on Europe's future is a citizen influence process on Europe's future.", 'The consultations will be done online and offline and bring together citizens, civil society and EU institutions.', 'With this in mind, for each of the following promotional messages, do you agree or not with the claims?', '{@ Q2_loop}', 'The message is clear', '{@ Q2_loop}', 'The message is credible', '{@ Q2_loop}', 'The message stands out in the campaign', '{@ Q2_loop}', 'The message is informative.', '{@ Q2_loop}', 'The message is inspiring.', 'According to your opinion, which of the 3 promotional announcements best conveys that you as a citizen can participate in the conference on the future of Europe?', 'For each of the following promotional notification how likely or incredible is that you would tell friends, family and family or colleagues about the conference on the future of Europe?', '{@}', "For each of the following promotional notification how likely or incredible, it is to search for more information about the conference on Europe's future?", '{@}', "For each of the following promotional notification how likely or incredible, it would be to participate in the conference on Europe's future?", '{@}', 'For each of the following promotional messages, do you agree or not that the message has the right tone to communicate with citizens as yourself?', '{@}', "Below, we show 3 promotional messages with different text that can be used to communicate about the conference on Europe's future.", '{# Q0a} {# q0b}', 'Which of the 3 promotional announcement do you like the most?', 'Which of the 3 promotional messages contributes most to an innovative picture of the European Union, in your opinion?', 'And which of the 3 promotional messages best shows that the European Union listens to its citizens?', 'Below we show 3 hash tags that may be used to advertise the conference on the future of Europe.', 'How much do you like these hash tags?', 'Hashtaggar or tags that start with the square symbol (#) are used on social media that twitter as a form of tagging that makes it possible to easily find or share content about a substance.', 'Very much', 'Quite', 'Not especially', "Doesn't like it at all", 'If you look at the 3 hashtaggar below which do you think is most effective?', 'None of the above', 'Do not know', 'Would you use any of the said hashtags on social media?', 'Yes, to read content about the conference on the future of Europe', 'Yes, to share or publish content about the conference on the future of Europe', 'No, I would not engage in this subject on social media', "No I don't use social media", 'Do not know', 'Device used to carry out the survey', 'Desktop computer, laptop', 'Smartphone.', 'Thank you for attending this survey.', 'During the next week, Ipsos plans to contact people who participated in more detail some key issues arising from this research using small group discussions online.', 'You will get a small compensation.', 'Would you like to be contacted again by Ipsos for this follow-up research?', 'Yes I want to be contacted to participate in smaller group discussions online', "No I don't want to be contacted to participate in smaller group discussions online", 'Thank you very much for your interest in participating in follow-up discussions in smaller groups online.', 'Are you available on any of the following dates and times?', 'You will obviously be able to thank you when we send the invitation.', '24.', 'March 2021, 17.00-18.00', '25.', 'March 2021, 17.00-18.00', "No I'm not available the dates", 'Thank you so much for attending the survey.', 'We appreciate you to take the time.', 'Agrees entirely', 'Tend to agree with', 'Tend to take distance', 'Takes completely distance', 'Do not know', 'The future is not written yet', "Create Europe's future", 'The future rests in your hands', 'Very likely', 'Likely', 'Unbelievable', 'Very incredible', 'Do not know', '#DriptDinframe.', '#Europa future.', '# Detached']

        if mt == None:
            logging.error("Something went wrong with the MT engine")
            logging.warning("Create list of empty transations")
            mt = [None] * len(clean_list)

        #mt.insert(0, 'MT') # adds label as first row
        mt.insert(0, mt_col_name) # adds label as first row
        sub_df.insert(3, mt_col_name, pd.Series(mt), allow_duplicates=True) # arg 1 is after which column it is inserted
        #print(sub_df.columns)
        sub_df.columns = ['Seg #', src_col_name, tr_col_name, mt_col_name]
        #print(sub_df) # now has one more column
        list_of_dfs.append(sub_df)

    # merge all dataframes for all files in the project
    proj_df = pd.concat(list_of_dfs)
    # Segment numbers have been extracted as floats, turn them to int
    proj_df = proj_df.astype({'Seg #': int})
    # Use the column of segment numbers as the new index
    proj_df = proj_df.set_index('Seg #')[0:]

    logging.info("---- This is the new proj_df:")
    logging.info(proj_df)

    logging.info("---- Returning from function: add_backxlats_to_proj_df()")
    return proj_df


if __name__ == '__main__':

    # get constants
    stages, stages_short, omt_prj_name_tmpl = define_constants()

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
            #df.iloc[0, 4] = "segid"
            sub_df = df.iloc[1:, 1:4] # rows, cols // get only seg#, src, tgt
            xlf_dict = list(sub_df.to_dict(orient='index').values()) # remove values to keep segment numbers
            file_data = {stage: xlf_dict}
            sorted_data[basename].update(file_data)
            #pprint.pprint(file_data)
            print("-------------------------------------------")
    
    pprint.pprint(sorted_data)

    

    




    # dictionary with orig 
    # add edit to orig dict
    
    #print(f'origin is {origin}')
    #data = pd.read_excel(origin)
    #print(data)