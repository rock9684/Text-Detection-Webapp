# ECE1779_Lab1

## Execution
To run the web app, either run command "flask run" (non-debug mode), "./start.sh" (non-debug gunicorn) or "python3 A1.py" (debug mode).  
Note: In "A1.py", debug mode is turned on by seeting "debug=True". This can affect the regular debugger you use.  

## Structure
The flask instance is declared in "app/\_\_init\_\_.py", which also imports routes declared in app.
  
This Flask instance is imported in "A1.py", and by running "A1.py" we run the instance.
  
To link new webpages, add new routes in "app/routes.py".  
 
All html files should be added into "app/templates" folder.  
  
Common html code that will appear on every webpage should go into "app/templates/base.html"  -> new html files should include this base page by adding "{% extends "base.html" %}"; new content will need to be include between "{% block content %}" and {% endblock %}.
  
## Coding
In html files, what enclosed in {{...}} is placeholder for dynamic content that is variable and will only be known at runtime.
  
If making a webpage taking user input, remember to include the methods in route delaration: "@webapp.route('/func_name', **methods=['GET', 'POST'])**", otherwise will be prompted to "method not allowed".
