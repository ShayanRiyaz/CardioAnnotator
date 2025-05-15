

# Current Work:

![image](https://github.com/user-attachments/assets/e0beff56-9ec1-46d8-871a-36df3b89460d)



# Instructions:



```
# cd into django project
cd  analysis_dashboard 
```


``` 
#1. From the folder containing environment.yml:
conda env create -f environment.yml 
```
```
python manage.py migrate
python manage.py runserver

```


# Proposed Universal Schema

```
fix: {
    subj_id
    rec_id
    files
    af_status
    subject_notes
},
ppg: {
    v
    fs
    method
    label
},
ekg: {
    v
    fs
    method
    label
},
bp: {
    v
    fs
    method
    label
    }
```
