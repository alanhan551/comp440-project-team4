import mysql.connector
from mysql.connector import errorcode
import PySimpleGUI as sg


DB_NAME = 'course_project'

TABLES = {}

TABLES['user'] = (
    "CREATE TABLE IF NOT EXISTS `user` ("
    "   `username` VARCHAR(32) NOT NULL ,"
    "   `password` VARCHAR(32) NOT NULL ,"
    "   `firstName` VARCHAR(32) NOT NULL ,"
    "   `lastName` VARCHAR(32) NOT NULL ,"
    "   `email` VARCHAR(64) NOT NULL ,"
    "   PRIMARY KEY (`username`),"
    "   UNIQUE KEY `email_UNIQUE`(`email`),"
    "   UNIQUE `username_UNIQUE` (`username`)"
    "  ) ENGINE = InnoDB DEFAULT CHARSET=utf8mb4" 
)

add_users = ("INSERT INTO user "
             "(username, password, firstName, lastName, email) "
             "VALUES ('test1', 'testpassword1', 'Bob', 'Smith', 'bob.smith@gmail.com'), "
             "       ('test2', 'testpassword2', 'Amanda', 'Walters', 'amanda.walters@gmail.com'), "
             "       ('test3', 'testpassword3', 'Denise', 'Belair', 'denise.belair34@yahoo.com'), "
             "       ('test4', 'testpassword4', 'Richard', 'Spacey', 'richard.spacey@gmail.com'), "
             "       ('test5', 'testpassword5', 'Curtis', 'Lee', 'curtis.lee@gmail.com')")

truncate_table = "TRUNCATE TABLE user"

# Connect to server
cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    port=3306,
    password="varsenik01",
    database=DB_NAME)

# Get a cursor
cursor = cnx.cursor(buffered=True)

# Use 'course_project' database, or create it if 'course_project' database does not alreay exist.
def init_database():
    try:
        # Initialize 'course_project' database
        cursor.execute("""Use %s""", (DB_NAME,))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = DB_NAME
        else:
            window['-status-'].update("Error: {}".format(err), visible=True)
    finally:
        create_tables()

# Create database
def create_database():
    try:
        cursor.execute("""CREATE DATABASE %s DEFAULT CHARACTER SET 'utf8mb4'""", (DB_NAME,))
    except mysql.connector.Error as err:
        window['-status'].update("Failed creating database: {}".format(err), visible=True)

# Create table(s)
def create_tables():
    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            cursor.execute(table_description)
            create_default_users()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                create_default_users()
            else:
                print("Failed creating table '{}': {}".format(table_name, err))
            
# Insert default users
def create_default_users():
    try:
        cursor.execute(truncate_table)
        cursor.execute(add_users)
        
        # Make sure data is committed to the database
        cnx.commit()
        window['-status-'].update('Database initialized.', visible=True)
    except mysql.connector.Error as err:
        window['status-'].update("Failed inserting default users: {}".format(err))

# Verify row exists within 'user' table
def login(login_event, data):
    valid_inputs = False
    valid_inputs = validate_inputs(login_event, data)
    
    if valid_inputs:
        try:
            data_login = (data['-login_username-'], data['-login_password-'])
            cursor.execute("SELECT firstName, lastName FROM user WHERE username=%s AND password=%s", data_login)
            if cursor.rowcount == 0:
                window['-login_status-'].update("Failed to log in - incorrect username or password.", visible=True)
            else:
                for (fname, lname) in cursor:
                    login_success(fname, lname)
        except mysql.connector.Error as err:
            window['-login_status-'].update("Failed to login: {}".format(err), visible=True)

def search(search_event,data):
    data_entered = (data['-category-'],)
    cursor.execute("Select* FROM item where category=%s", data_entered)
    result = cursor.fetchall()

# Insert user inputted data into new row within table 'user'
def register(register_event, data):
    valid_inputs = False
    valid_username = False
    valid_password = False
    valid_email = False

    valid_inputs = validate_inputs(register_event, data)
    if valid_inputs:
        valid_username = validate_username(data['-register_username-'])
        
    if valid_username:
        valid_password = validate_password(data['-register_password-'], data['-register_password2-'])
        
    if valid_password:
        valid_email = validate_email(data['-email-'])
        
    if valid_email:
        try:
            data_user = (data['-register_username-'], data['-register_password-'], data['-fname-'], data['-lname-'], data['-email-'])
            cursor.execute("""INSERT INTO user (username, password, firstName, lastName, email) VALUES (%s, %s, %s, %s, %s)""", data_user)

            # Make sure data is committed to the database
            cnx.commit()
            
            register_success()
        except mysql.connector.Error as err:
            window['-status-'].update("Failed to register user: {}".format(err), visible=True)

# Clear input fields
def clear_inputs(data):
    for input in data:
        window[input].update('')
        
# Initialize buttons in Login page
def init_login_buttons():
    window['B_LOGIN'].update(visible=True)
    window['B_LOGIN_CANCEL'].update(visible=True)
    window['B_LOGIN_HOME'].update(visible=False)


# Initialize buttons in Registration page
def init_register_buttons():
    window['B_REGISTER'].update(visible=True)
    window['B_REGISTER_CANCEL'].update(visible=True)
    window['B_REGISTER_HOME'].update(visible=False)

def search_button():
    window['B_SEARCH'].update(visible=True)
    window['B_LOGIN_CANCEL'].update(visible=False)
    window['B_LOGIN_HOME'].update(visible=True)


def login_success(firstName, lastName):
    window['-login_status-'].update("Successfully logged in. Welcome back, {} {}!".format(firstName, lastName), visible=True)
    window['B_LOGIN'].update(visible=False)
    window['B_LOGIN_CANCEL'].update(visible=False)
    window['B_LOGIN_HOME'].update(visible=True)


def register_success():
    window['-registration_status-'].update("Registration successful.", visible=True)
    window['B_REGISTER'].update(visible=False)
    window['B_REGISTER_CANCEL'].update(visible=False)
    window['B_REGISTER_HOME'].update(visible=True)

# Validate inputs
def validate_inputs(event, data):
    if event == 'B_LOGIN':
        for input in ('-login_username-', '-login_password-'):
            if len(data[input]) == 0:
                window['-login_status-'].update('Field(s) cannot be left blank.', visible=True)
                return False
            elif len(data[input]) > 32:
                window['-login_status-'].update('Field cannot exceed 32 characters.', visible=True)
                return False
    else:
        for input in ('-register_username-', '-register_password-', '-register_password2-', '-fname-', '-lname-', '-email-'):
            if len(data[input]) == 0:
                window['-registration_status-'].update("Field(s) cannot be left blank.", visible=True)    
                return False
            elif input == '-email-' and len(data[input]) > 64:
                window['-registration_status-'].update('Email cannot exceed 64 characters.', visible=True)
                return False
            elif len(data[input]) > 32:
                window['-registration_status-'].update('Field cannot exceed 32 characters.', visible=True)
                return False
    return True

# Validate password
def validate_password(password, repeat_password):
    isValid = True
    if (password != repeat_password):
        isValid = False
        window['-registration_status-'].update('Passwords do not match.', visible=True)
    return isValid
    
# Validate username
def validate_username(username):
    isValid = True
    try:
        # Check if any rows in 'user' table contain user inputted username
        cursor.execute("""SELECT COUNT(*) AS count FROM user WHERE username=%s""", (username,))
        for (count,) in cursor:
            if count > 0:
                window['-registration_status-'].update("Username '{}' is already in use.".format(username), visible=True)
                isValid = False
    except mysql.connector.Error as err:
        window['-registration_status-'].update("Failed validating username: {}".format(err), visible=True)
        isValid = False
        
    return isValid

# Validate email
def validate_email(email):
    isValid = True
    try:
        # Check if any rows in 'user' table contain user inputted email
        cursor.execute("""SELECT COUNT(*) AS count FROM user WHERE email=%s""", (email,))
        for (count,) in cursor:
            if count > 0:
                window['-registration_status-'].update("Email '{}' is already in use.".format(email))
                isValid = False
    except mysql.connector.Error as err:
        window['-registration_status-'].update('Failed validating email: {}'.format(err))
        isValid = False
        
    return isValid

sg.theme('DarkAmber') # Add a theme of color
# All the stuff inside the window
layout_initialize = [
    [sg.Button('Initialize Database', key='B_INIT_DB')],
    [sg.Button(button_text='Login', key='B_INIT_LOGIN'), sg.Button('Register', key='B_INIT_REGISTER')],
    [sg.Button(button_text='Search', key='B_SEARCH')],
    [sg.Text('', key='-status-', visible=False)]
]

layout_register = [
    [sg.Text('Username'), sg.InputText(key='-register_username-')],
    [sg.Text('Password'), sg.InputText(key='-register_password-')],
    [sg.Text('Re-enter password'), sg.InputText(key='-register_password2-')],
    [sg.Text('First Name'), sg.InputText(key='-fname-')],
    [sg.Text('Last Name'), sg.InputText(key='-lname-')],
    [sg.Text('E-mail'), sg.InputText(key='-email-')],
    [sg.Button(button_text='Submit', key='B_REGISTER'), sg.Button('Cancel', key='B_REGISTER_CANCEL'), sg.Button('Home', key='B_REGISTER_HOME', visible=False)],
    [sg.Text('', key='-registration_status-', visible=False)]
]

layout_login = [
    [sg.Text('Username'), sg.InputText(key='-login_username-')],
    [sg.Text('Password'), sg.InputText(key='-login_password-')],
    [sg.Button(button_text='Submit', key='B_LOGIN'), sg.Button('Cancel', key='B_LOGIN_CANCEL'), sg.Button('Home', key='B_LOGIN_HOME', visible=False)],
    [sg.Text('', key='-login_status-', visible=False)]
]

layout_search = [
    [sg.Text('Search'), sg.InputText(key='-category-')],
    [sg.Button(button_text='Search', key='B_SEARCH'), sg.Button('Cancel', key='B_SEARCH_CANCEL')]
]


layout = [
    [
        sg.Column(layout_initialize, key='-INITIALIZE-'),
        sg.Column(layout_register, visible=False, key='-REGISTER-'),
        sg.Column(layout_login, visible=False, key='-LOGIN-'),
        sg.Column(layout_search, visible=False, key='-SEARCH-')
    ]
]

# Create the Window
window = sg.Window('COMP 440 - Course Project (Part 1)', layout)

# Event loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED: # if user closes window
        cursor.close()
        cnx.close()
        break
    else:
        if event == 'B_INIT_LOGIN':
            # Display Login page
            init_login_buttons()
            window[f'-INITIALIZE-'].update(visible=False)
            window[f'-LOGIN-'].update(visible=True)
            window[f'-REGISTER-'].update(visible=False)
            window[f'-SEARCH-'].update(visible=False)
        elif event == 'B_INIT_REGISTER':
            # Display Registration page
            init_register_buttons()
            window[f'-INITIALIZE-'].update(visible=False)
            window[f'-LOGIN-'].update(visible=False)
            window[f'-REGISTER-'].update(visible=True)
            window[f'-SEARCH-'].update(visible=False)
        elif event == 'B_LOGIN': # User submits login credentials
            login(event, values)
        elif event == 'B_REGISTER': # User submits registration credentials
            register(event, values)
        elif event == 'B_INIT_DB': # User clicks 'Initialize Database' button
            init_database()
        elif event == 'B_SEARCH': # User enters text to search
            window[f'-INITIALIZE-'].update(visible=False)
            window[f'-LOGIN-'].update(visible=False)
            window[f'-REGISTER-'].update(visible=False)
            window[f'-SEARCH-'].update(visible=True)
        else:
            # Default: display home page
            clear_inputs(values)
            window['-login_status-'].update('', visible=False)
            window['-registration_status-'].update('', visible=False)
            window['-status-'].update('', visible=False)
            window[f'-INITIALIZE-'].update(visible=True)
            window[f'-LOGIN-'].update(visible=False)
            window[f'-REGISTER-'].update(visible=False)
            window[f'-SEARCH-'].update(visible=False)
window.close()