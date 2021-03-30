###### Python code to update the COVID-19 counts and sex/gender analysis candidate counts ######


import numpy as np
import pandas as pd
from datetime import datetime
import re
import warnings
warnings.filterwarnings("ignore")


###################################################################################################################################################

#  LOAD DATA, SOME PROCESSING

###################################################################################################################################################



###### Load the new data on studies submitted after creation of our existing dataset ######
# from separate R query of AACT PostgreSQL database
# change file paths if necessary
path=''

studies=pd.read_csv(path+'studies.csv',index_col=0)# all studies have a title
brief_summaries=pd.read_csv(path+'brief_summaries.csv',index_col=0)# almost all have brief summary, conditions and some outcomes
detailed_descriptions=pd.read_csv(path+'detailed_descriptions.csv',index_col=0)# about 70% in general have detailed description
conditions=pd.read_csv(path+'conditions.csv',index_col=0)
design_outcomes=pd.read_csv(path+'design_outcomes.csv',index_col=0)
design_groups=pd.read_csv(path+'design_groups.csv',index_col=0)
eligibilities=pd.read_csv(path+'eligibilities.csv',index_col=0)
interventions=pd.read_csv(path+'interventions.csv',index_col=0)
documents=pd.read_csv(path+'documents.csv',index_col=0)
provided_documents=pd.read_csv(path+'provided_documents.csv',index_col=0)



#merge the detailed summary and brief descriptions with studies df (to make life easier later)
studies=studies.merge(brief_summaries, how='left',left_on='nct_id',right_on='nct_id')
studies.rename(columns={"description": "brief_summary"},inplace=True)
studies=studies.merge(detailed_descriptions, how='left',left_on='nct_id',right_on='nct_id')
studies.rename(columns={"description": "detailed_description"},inplace=True)


# test pre-processing - remove hyphens and single space text
studies['official_title'] = studies['official_title'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)
studies['brief_title'] = studies['brief_title'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)
studies['brief_summary'] = studies['brief_summary'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)
studies['detailed_description']=studies['detailed_description'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)


###################################################################################################################################################

# DEFINE FUNCTION TO BUILD BOOLEAN MASKS TO PERFORM TEXT SEARCHES

###################################################################################################################################################


def mask_builder(df_name,col_name,search_terms):
    # Boolean mask; 
    # when applied to df, should return all rows with one or more of search terms in targeted column.
    # case-insensitive basic-substring search
    
    #impose that datafields are not null (else applying mask1 could break)
    mask0=df_name[col_name].notnull()
    #initiate mask1 as all False
    mask1=pd.Series(False,index=df_name.index)
    for i in search_terms:
        mask1=mask1+df_name[col_name].str.contains(search_terms[i],case=False,regex=True)
        #impose mask0 AND mask1 i.e discard rows with null values in col_name
        mask=mask0&mask1         
    return mask



###################################################################################################################################################

# CREATE COVID-19 SET : TEXT SEARCH

###################################################################################################################################################


# DEFINE DICTIONARY WITH COVID-19 TERMS

corona_terms={1:'coronavirus',2:'corona virus',3:'sars cov 2',4:'sars cov2',5:'sarscov2',6:'covid',7:'2019 ncov',8:'2019ncov'}



################################

# Titles

################################
## simple case insensitive substring search (so e.g will catch betacoronavirus, COVID19 etc.)
# field has to contain one or more of search terms to be counted as a match
# e.g here title must contain 'coronavirus' OR 'corona virus' OR........



corona_official_title=studies[mask_builder(studies,'official_title',corona_terms)]

corona_brief_title=studies[mask_builder(studies,'brief_title',corona_terms)]



################################

# Conditions

################################

#### First process the downcase name:
# remove hyphens and single space
conditions['downcase_name'] = conditions['downcase_name'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)


corona_conditions=conditions[mask_builder(conditions,'downcase_name',corona_terms)]

################################

# Outcome_measures - types= Primary, Secondary and Other

################################


# process columns of interest:
design_outcomes['measure'] = design_outcomes['measure'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)
design_outcomes['description'] = design_outcomes['description'].str.replace('-', ' ').str.replace('\s+', ' ', regex=True)



corona_meas=design_outcomes[mask_builder(design_outcomes,'measure',corona_terms)]
corona_des=design_outcomes[mask_builder(design_outcomes,'description',corona_terms)]

corona_outcomes=corona_meas.append(corona_des)

################################

# Brief Summaries

################################

#### already processed the downcase name, removed hyphens and single space


corona_brief=studies[mask_builder(studies,'brief_summary',corona_terms)]



################################

# Detailed descriptions

################################
#### already processed the downcase name, removed hyphens and single space


corona_detailed=studies[mask_builder(studies,'detailed_description',corona_terms)]


###################################################################################################################################################

# CREATE COVID-19 SET : MERGE SEARCH RESULTS

###################################################################################################################################################



###### Merge the corona_title results #######
corona_studies=corona_brief_title.append(corona_official_title)


###### Merge the corona results: conditions #######
corona_studies=corona_studies.append(studies[studies['nct_id'].isin(corona_conditions['nct_id'])])

###### Add primary outcomes: ######
corona_primary=corona_outcomes[corona_outcomes['outcome_type']=='primary']
corona_studies=corona_studies.append(studies[studies['nct_id'].isin(corona_primary['nct_id'])])

###### Add in those with covid term in SO/OO AND brief summary ######
corona_SO_OO=corona_outcomes[corona_outcomes['outcome_type']!='primary'] # make df of SO and OO only

# df of those with covid matches in outcomes and brief summary
corona_SO_OO_brief=studies[(studies['nct_id'].isin(corona_SO_OO['nct_id']))&(studies['nct_id'].isin(corona_brief['nct_id']))]

#append to existing set:
corona_studies=corona_studies.append(corona_SO_OO_brief)

###### Add in those with covid term in brief summary AND detailed description ######

#both were built from studies df, so can just inner merge:
corona_brief_detailed=corona_brief.merge(corona_detailed, how='inner', left_on='nct_id',right_on='nct_id')

#append to existing set:
corona_studies=corona_studies.append(corona_brief_detailed)
corona_studies=corona_studies.drop_duplicates(subset='nct_id') # will have had many overlaps in appended results - drop duplicates

###################################################################################################################################################

# CREATE COVID-19 SET : DATA CLEANING

###################################################################################################################################################



###### Starting on/after Jan 1, 2020 ######

# not all studies list a start date, all have a submitted date
# our datset was all studies starting on/after Jan 1, 2020, 
# or if no start date available first submitted on/after Jan 1, 2020

# here in this update we should only have studies submitted on/after Jan 1 2021 (alow some overlap)
# BUT must reimpose start date condition as some studies do get subimtted to CT.gov (long) after they have started
# AACT standardises start dates in YYY-MM-DD format

corona_studies=corona_studies[(corona_studies['start_date']>='2020-01-01')|(corona_studies['start_date'].isnull())]


###### study status selection ######

# withdrawn studies are those cancelled before first patient enrolled

corona_studies=corona_studies[(corona_studies['overall_status']!='Withdrawn')&(corona_studies['overall_status']!='No longer available')]

###### Duplicates ######
# CT.gov should take care of removing them, but only deals with most obvious e.g those accidentally entered twice
# AACT only incorporates those changes on a monthly basis
# We expect there will be (and have spotted) studies in there that are only trivially different
# and for some reason were resubmitted instead of just updating current record and so on.
# we will look for an remove the most obvious duplicates i.e those with exact same titles and brief summaries
# Our existing cleaned dataset of 4420 studies may have some duplicates from January still in there
# that AACT has now removed, we do not update to account for that here

# df of the first appearance of each duplicate
real_duplicates=corona_studies[corona_studies.duplicated(subset=['official_title','brief_summary'],keep='first')]
# all duplicated studies (in case there are triplicates etc.)
all_duplicates=corona_studies[corona_studies.duplicated(subset=['official_title','brief_summary'],keep=False)]
#reomve all coourences of studies that are duplicated
final_corona=corona_studies[~corona_studies['nct_id'].isin(all_duplicates['nct_id'])]
# add back in only the first occurence of each
final_corona=final_corona.append(real_duplicates)


###################################################################################################################################################

# CREATE COVID-19 SET : IMPORT EXISTING STUDIES

###################################################################################################################################################


###### print the number of new studies since we did our last full auto and manual run through #####

#remove any overlap with our existing COVID set source_data.xlsx, ct.gov sample sheet
existing_corona=pd.read_excel('source_data.xlsx','ct.gov_sample')


# Latest submission date in our final 2020 sample was Jan 15, 2021
# we allowed couple of weeks overlap in new query
# just in case some studies had significant lags between first submitting to CT.gov and actually being posted there
# (there is a short quality control review process between submittting and posting - usually couple of days)

new_corona=final_corona[~final_corona['nct_id'].isin(existing_corona['nct_id'])]

## print lastest and earliest submission date in new numbers
#new_corona['study_first_submitted_date'].min()
#new_corona['study_first_submitted_date'].max()




###################################################################################################################################################

# CREATE SEX/GENDER CANDIDATES  SET : SEPARATE OUT SINGLE SEX STUDIES

###################################################################################################################################################




# ID single sex studies and those where all sexes eligible (by design) using CT.gov 'Sex' (eligible for study) element
# In the AACT it's the 'gender' column in eligibilities table
# only look for occurences of sex/gender terms in records of studies where all sexes eligible:
new_corona=new_corona.merge(eligibilities[['nct_id','gender']],how='left',left_on='nct_id',right_on='nct_id')
new_corona_all=new_corona[new_corona['gender']=='All']
new_corona_F=new_corona[new_corona['gender']=='Female']
new_corona_M=new_corona[new_corona['gender']=='Male']


###################################################################################################################################################

# CREATE SEX/GENDER CANDIDATES  SET : TEXT SEARCH

###################################################################################################################################################

# DEFINE DICTIONARY WITH SEX TERMS
# tailor the terms for input into search - since now we want regular expressions - search for whole words, add the \b bounding conditions
# \b ensure that bounding characters of words cannot be alpha numeric characters

sex_terms={1:r'\bsex\b',2:r'\bsexes\b',3:r'\bgender\b',4:r'\bgenders\b',5:r'\bwoman\b',6:r'\bwomen\b',7:r'\bman\b',8:r'\bmen\b',9:r'\bfemale\b',10:r'\bfemales\b',11:r'\bmale\b',12:r'\bmales\b',13:r'\bgirl\b',14:r'\bgirls\b',15:r'\bboy\b',16:r'\bboys\b',17:'pregnan',18:'transg'}


################################

# Detailed Descriptions

################################
# most likely place to find description of planned (sex-based) analysis

### Search text for the terms. Text must have one of the keyword possibilities.
## case insensitive regex search with boundary characters for terms (so match only whole words)


SG_detailed=new_corona_all[mask_builder(new_corona_all,'detailed_description',sex_terms)]

################################

# Brief Summaries

################################


SG_brief=new_corona_all[mask_builder(new_corona_all,'brief_summary',sex_terms)]



################################

# Titles

################################

SG_official_title=new_corona_all[mask_builder(new_corona_all,'official_title',sex_terms)]


SG_brief_title=new_corona_all[mask_builder(new_corona_all,'brief_title',sex_terms)]


################################

# Outcomes -  Primary, Secondary, Other

################################

###### SEARCH THE DESIGN OUTCOMES (PRIMARY, SECONDARY AND OTHER) ######

#limit to searching the outcome measures of the identified new COVID-19 studies
# amd the 'measure' and 'description' columns in the table

new_design=design_outcomes[design_outcomes['nct_id'].isin(new_corona_all['nct_id'])]


SG_new_design_measure=new_design[mask_builder(new_design,'measure',sex_terms)]

# table has more than one row per study
# intead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_outcomes_measure=new_corona_all[new_corona_all['nct_id'].isin(SG_new_design_measure['nct_id'])]



SG_new_design_description=new_design[mask_builder(new_design,'description',sex_terms)]
# table has more than one row per study
# intead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_outcomes_description=new_corona_all[new_corona_all['nct_id'].isin(SG_new_design_description['nct_id'])]

################################

# Design Groups

################################
# here have titles and descriptions of the study arms/groups
# might expect to see statements about sex matching, sex-representative groups etc. and recruitment here


#limit to searching the outcome measures of the identified new COVID-19 studies
# amd the 'title' and 'description' columns in the table

new_design_groups=design_groups[design_groups['nct_id'].isin(new_corona_all['nct_id'])]


SG_new_design_groups_description=new_design_groups[mask_builder(new_design_groups,'description',sex_terms)]

# table has more than one row per study
# intead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_groups_description=new_corona_all[new_corona_all['nct_id'].isin(SG_new_design_groups_description['nct_id'])]


SG_new_design_groups_title=new_design_groups[mask_builder(new_design_groups,'title',sex_terms)]

# table has more than one row per study
# intead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_groups_title=new_corona_all[new_corona_all['nct_id'].isin(SG_new_design_groups_title['nct_id'])]


################################

# Eligibilities

################################
# mostly will get hits here related to recruitment



new_eligibilities=eligibilities[eligibilities['nct_id'].isin(new_corona_all['nct_id'])]

# gender_description column is rarely used but often contains relevant info, do not search, just add all
SG_eligibilities_gender_description=new_eligibilities[new_eligibilities['gender_description'].notnull()]
SG_gender_description=new_corona_all[new_corona_all['nct_id'].isin(SG_eligibilities_gender_description['nct_id'])]

# population field: describes the eligibile population draw participants from

SG_eligibilities_population=new_eligibilities[mask_builder(new_eligibilities,'population',sex_terms)]

# table has more than one row per study
# intead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_population=new_corona_all[new_corona_all['nct_id'].isin(SG_eligibilities_population['nct_id'])]


# criteria column includes a bullet point list of the inclusion and exclusion criteria 
# they must each be clearly labelled inclusion and exclusion 
# in our full paper sample this was so, and inclusion came first in almost every case
# we will test that here: (un-comment to run tests if you wish)

#print(len(new_eligibilities[new_eligibilities['criteria'].isnull()]), ' studies did not provide inclusion and exclusion criteria')

# to split up the text, make sure inclusion always comes before exclusion:
incl_excl=new_eligibilities[(new_eligibilities['criteria'].notnull())&(new_eligibilities['criteria'].str.contains('exclusion', case=False)) &(new_eligibilities['criteria'].str.contains('inclusion', case=False))  ]
#print(len(incl_excl))
# str.find does not have option to ignore case in text search
incl_excl['criteria']=incl_excl['criteria'].str.lower()
#test that inclusion criteria always come before exclusion criteria
# CODE MIGHT BREAK HERE OTHERWISE!!
#print(len(incl_excl[incl_excl['criteria'].str.find('inclusion')<incl_excl['criteria'].str.find('exclusion')]))
# now isolate the block of text that covers the inclusion criteria:
# we are not interested in looking at exclusion criteria (will be full of mentions of exclusing pregnant women etc.)
incl_excl['incl_criteria']=incl_excl['criteria'].apply(lambda x: x.split('inclusion')[1].split('exclusion')[0])
#print(len(incl_excl))
#print(len(incl_excl['incl_criteria'].notnull()))

#search the inclusion criteria for sex/gender terms:


SG_eligibilities_inclusion=incl_excl[mask_builder(incl_excl,'incl_criteria',sex_terms)]

# table has more than one row per study
# instead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_inclusion=new_corona_all[new_corona_all['nct_id'].isin(SG_eligibilities_inclusion['nct_id'])]

# note that this number here will be slightly dfferent compared to methodology in paper
# (there we also dealt with small number of studies where layout in this section was non-standard)



################################

#Interventions

################################
# mostly will get hits here related to recording/reporting sex/gender
# sometimes a questionnaire regarding sex/gender etc. is administered and reported as an intervention here

new_interventions=interventions[interventions['nct_id'].isin(new_corona_all['nct_id'])]


SG_interventions_description=new_interventions[mask_builder(new_interventions,'description',sex_terms)]

# table has more than one row per study
# intead select snapshot from studies table of matches returned from search (will aid with merging results)
SG_interventions=new_corona_all[new_corona_all['nct_id'].isin(SG_interventions_description['nct_id'])]


################################

# Provided Documents

################################
# can upload supporting documents in pdf form to CT.gov (provided documents)
# or provide an external link (documnets table)
# here we will count number that indicate those documents include a description of the statistical analysis plan
# we do not ID which have sex/gender keywords in the text in this pipeline

new_documents=documents[documents['nct_id'].isin(new_corona_all['nct_id'])]
new_provided_documents=provided_documents[provided_documents['nct_id'].isin(new_corona_all['nct_id'])]

#search the documents belonging to the new corona studies for inclusion of statistical analysis plans:
# the AACT includes a has_sap (stat. analysis plan.) tag in the provided documents table, we'll use that here
SAP_provided_doc=new_provided_documents[new_provided_documents['has_sap']==True]
SAP_doc=new_documents[new_documents['document_type'].str.contains('statistical', case=False)]

#merge results of searching two tables:
SAP=new_corona_all[new_corona_all['nct_id'].isin(SAP_provided_doc['nct_id'])].append(new_corona_all[new_corona_all['nct_id'].isin(SAP_doc['nct_id'])])
SAP=SAP.drop_duplicates(subset='nct_id')

###################################################################################################################################################

# CREATE SEX/GENDER CANDIDATES  SET : MERGE SEARCH RESULTS

###################################################################################################################################################



###### Merging results of field searches ######


# numbers of candidates for sex/gender analysis/matching/recruitment/recording/representation etc.
#                       amongst studies where all sexes eligible to participate
# list of results of searching all relevant tables for sex keywords: (SG_inclusion kept separate)
search_results=[SG_detailed, SG_brief, SG_official_title, SG_brief_title, SG_outcomes_measure, 
                SG_outcomes_description, SG_groups_description, SG_groups_title, SG_gender_description,
               SG_population, SG_interventions]
#concatenate all the results
sex_candidates=pd.concat(search_results)
#deal with overlaps - drop duplicates
sex_candidates=sex_candidates.drop_duplicates(subset='nct_id')


# ID those studies that ONLY have a sex term in the eligibilities inclusion criteria and all sexes eligible:
inclusion_crit_only=SG_inclusion[~SG_inclusion['nct_id'].isin(sex_candidates['nct_id'])]


print(new_corona['nct_id'].nunique(), ' new COVID-19 study candidates since last AACT query (2021-01-26)')

print(len(new_corona_M)+len(new_corona_F),'are designed as single sex studies', len(new_corona_M), 'male and' , len(new_corona_F), ' female.')
print('All sexes are eligibile for the remainder of the studies')
print(len(sex_candidates),' of these are candidates for attention to sex/gender at level of analysis/reporting/sex-matching/recruiting. Some will be spurious matches')
print( 'A further',len(inclusion_crit_only) , 'are ONLY recruitment candidates i.e had a sex/gender term only in the eligibities incluion criteria section of the registration')
print( len(SAP), ' of the new non single-sex studies studies have uploaded a statistical analysis plan or provided a link to one') 
