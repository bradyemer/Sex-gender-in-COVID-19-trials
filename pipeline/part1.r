#R code to query the AACT cloud PostgreSQL database for new studies

#- Querying the cloud database requires creating your own AACT user account - insert your username and password in code below
#- Here we take only the 2021 snapshot of the tables necessary for updating the COVID-19 study and sex/gender candidates counts
#- Will query for all studies submitted to ClinicalTrials.gov on/after Jan 1, 2021
#- The latest submission date in our exsiting sample was Jan 15, 2021, we allow for a couple of weeks overlap to catch any studies whose quality control review (which takes place before a submitted study is posted on CT.gov) was taking longer than average. You can extend this if you wish by changing the date 
#- Note that to create our full dataset we queried for all studies with start date on/after Jan 1 2020 or (since not all have a start date) with a study first submitted date on/after Jan 1, 2020


install.packages("RPostgreSQL",repos='https://mirrors.dotsrc.org/cran/') 
library(RPostgreSQL)
drv <- dbDriver('PostgreSQL')

#connect with your login details
username <- "insert your username here"
your_password <- "insert your password here"
con <- dbConnect(drv, dbname="aact",host="aact-db.ctti-clinicaltrials.org", port=5432, user=username, password=your_password)


#download the necessary tables (all columns) - preserve table name
#Define path to destination directory:
destination_directory <- "AACT_data/"

#Start by downloading the core 'studies' table:
aact_studies <- dbGetQuery(con, "select * from studies where study_first_submitted_date>='2021-01-01'  ")
write.csv(aact_studies, file=paste(paste(destination_directory,"studies",sep=""),".csv",sep=""))

#now loop over remaining tables of interest:

tables<-list("conditions","provided_documents","design_outcomes","eligibilities","design_groups",
"interventions","detailed_descriptions","brief_summaries")

for (table_name in tables)
{
	sql_query<-paste(paste("select * from",table_name, sep=" "),"where nct_id in (select nct_id from studies where study_first_submitted_date>='2021-01-01') "),sep=" ")
	file_path<-paste(paste(destination_directory,item,sep=""),".csv",sep="")
	temp_csv<- dbGetQuery(con, sql_query)
	write.csv(temp_csv, file=file_path)
}



