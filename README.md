DataloggR

Software to work with the RTI Datalogger

# Run Application
Run the application by running app.py
 * This will start a Flask Server and open the web browser
 * The application will then interact between app.py and the web browser

# Dependencies
Dependencies are found in requirements.txt
```bash
pip install -r requirements.txt
pip install -r rti_python\requirements.txt
```

# VSCode to run Python scripts to activate VENV
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
& c:/Users/rico/Documents/rti/python/DataloggR/venv/Scripts/Activate.ps1
```


# Debugging Code
Open the application and press Ctrl-Shift-I to view the Chrome Inspection Tool.  

If the Javascript is modified, the previous script will be in cache and not relead.
Go to the Network tab in the Chrome inspection tool and check and uncheck "Disable Cache".
Then reload the browser window by pressing Ctrl-R.  The new Javascript will be loaded and you can verify this in the Console tab of the inspection tool.  

You can also debug the javascript in the Inspection tool

# Code Layout
## app.py
app.py hosts the python Flask server backend.  The backend handles all the button clicks and datalogger connections.

##main.js
main.js is an AJAX javascript.  It handles all the GUI.  It also displays the status of the datalogger.  Any button clicks will be sent to the python backend at app.py.

##Static folder
This folder holds the javascript file and images.

##Template
This folder holds all the GUI HTML jinja displays.  Jinja the template engine for the Flask python server.  Within the Jinja template files, the javascript files will handle the dynamic displaying. 