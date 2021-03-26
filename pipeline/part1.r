#R code to query the AACT cloud PostgreSQL database for new studies

#- Querying the cloud database requires creating your own AACT user account - insert your username and password in code below
#- Here we take only the 2021 snapshot of the tables necessary for updating the COVID-19 study and sex/gender candidates counts
#- Will query for all studies submitted to ClinicalTrials.gov on/after Jan 1, 2021
#- The latest submission date in our existing sample was Jan 15, 2021, we allow for a couple of weeks overlap to catch any studies whose quality control review (which takes place before a submitted study is posted on CT.gov) was taking longer than average. You can extend this if you wish by changing the date 
#- Note that to create our full dataset we queried for all studies with start date on/after Jan 1 2020 or (since not all have a start date) with a study first submitted date on/after Jan 1, 2020

install.packages("RPostgreSQL",repos='https://mirrors.dotsrc.org/cran/') 
library(RPostgreSQL)
drv <- dbDriver('PostgreSQL')
con <- dbConnect(drv, dbname="aact",host="aact-db.ctti-clinicaltrials.org", port=5432, user="", password="")#connect with your login details

#download the necessary tables (all columns) - preserve table name, change write file path as necessary

aact_studies <- dbGetQuery(con, "select * from studies where study_first_submitted_date>='2021-01-01'  ")
write.csv(aact_studies, file='studies.csv')

aact_brief_summaries <- dbGetQuery(con, "select * from brief_summaries where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_brief_summaries, file='brief_summaries.csv')

aact_detailed_descriptions <- dbGetQuery(con, "select * from detailed_descriptions where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_detailed_descriptions, file='detailed_descriptions.csv')

aact_conditions <- dbGetQuery(con, "select * from conditions where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_conditions, file='conditions.csv')

aact_design_outcomes <- dbGetQuery(con, "select * from design_outcomes where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_design_outcomes, file='design_outcomes.csv')

aact_design_groups <- dbGetQuery(con, "select * from design_groups where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_design_groups, file='design_groups.csv')

aact_eligibilities <- dbGetQuery(con, "select * from eligibilities where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_eligibilities, file='eligibilities.csv')

aact_interventions <- dbGetQuery(con, "select * from interventions where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_interventions, file='interventions.csv')

aact_documents <- dbGetQuery(con, "select * from documents where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_documents, file='documents.csv')

aact_provided_documents <- dbGetQuery(con, "select * from provided_documents where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') ")
write.csv(aact_provided_documents, file='provided_documents.csv')
