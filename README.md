# Dispecerat 112

A desktop app for managing emergency calls (112) and the interventions sent in response: ambulance, fire brigade, police and mountain rescue.

Built with **Python (Tkinter)** and a **MySQL** database I designed myself (10 related tables). University project for my *Databases* course. The interface is in Romanian.

## Features

- Operator login and account creation
- Add new calls and update their status live
- Track interventions, staff, equipment and reports
- Search through every table
- Statistics and charts (calls per month and year, busiest units, most common incidents)

## How to run

```bash
mysql -u root -p < database/schema.sql
pip install -r requirements.txt
python src/app.py
```

Demo login: `demo` / `demo123`

## Author

Alexandra Zahiu
