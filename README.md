# FT21 to MS22 transfer check

## Module versionss

Written and tested with the following modules:

- Python 3.8.5
- pip 20.0.2
- pandas 1.2.4
- requests 2.22.0
- XlsxWriter 1.4.3

## Preparation

For every version that needs to be processed, unpack the two OmegaT projects (FT and MS versions) in a folder, e.g.:

```
souto@ameijoa$ tree -L 1 path/to/files/ara-ISR/
path/to/files/ara-ISR/
├── PISA2021FT_ara-ISR_OMT_Questionnaires
├── PISA2021FT_ara-ISR_OMT_Questionnaires.omt
├── PISA2022MS_ara-ISR_OMT_Questionnaires
└── PISA2022MS_ara-ISR_OMT_Questionnaires.omt

2 directories, 2 files
```

The script `write_project2excel.groovy` must be run on each of the two OmegaT projects. 

This can be automated on the command line, like so:

```
java -jar /path/to/omegat/OmegaT.jar path/to/project-folder --mode=console-translate --script=/path/to/scripts/write_project2excel.groovy
```

## Execution

You can call this script as:

```
python path/to/code/main.py -l xxx-XXX -p path/to/files/xxx-XXX
```

where `xxx-XXX` is the version you want to handle and `path/to/files/xxx-XXX` leads to the folder that contains the two unpacked projects referred to above.

For example: 

```
python path/to/code/main.py -l ara-ISR -p path/to/files/ara-ISR
```

