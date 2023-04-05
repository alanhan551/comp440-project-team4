import mysql.connector
from mysql.connector import errorcode
import PySimpleGUI as sg

DB_NAME = 'course_project'

TABLES = {}

DEFAULT_ROWS = {}

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

TABLES['item'] = (
    "CREATE TABLE IF NOT EXISTS `item` ("
	"   `id` INT NOT NULL AUTO_INCREMENT,"
    "   `title` varchar(32) NOT NULL,"
    "   `description` varchar(64) NOT NULL,"
    "   `category` varchar(255) NOT NULL,"
    "   `price` DECIMAL(16,2) NOT NULL,"
    "   `insert_user` varchar(32) NOT NULL,"
    "   `insert_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
    "   PRIMARY KEY (`id`),"
    "   FOREIGN KEY(`insert_user`) REFERENCES `user`(`username`),"
    "   UNIQUE KEY `item_id_UNIQUE` (`id`)"
    "  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

DEFAULT_ROWS['user'] = (
    "INSERT INTO user "
    "(username, password, firstName, lastName, email) "
    "VALUES ('test1', 'testpassword1', 'Bob', 'Smith', 'bob.smith@gmail.com'), "
    "       ('test2', 'testpassword2', 'Amanda', 'Walters', 'amanda.walters@gmail.com'), "
    "       ('test3', 'testpassword3', 'Denise', 'Belair', 'denise.belair34@yahoo.com'), "
    "       ('test4', 'testpassword4', 'Richard', 'Spacey', 'richard.spacey@gmail.com'), "
    "       ('test5', 'testpassword5', 'Curtis', 'Lee', 'curtis.lee@gmail.com')"
)

DEFAULT_ROWS['item'] = (
    "INSERT INTO item "
    "(title, description, category, price, insert_user) "
    "VALUES ('Smartphone', 'This is the new iPhone X', 'electronic, cellphone, apple', 1000, 'test1')"
)

current_user = None

# Connect to server
cnx = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="alanhan",
    password="Superduperpassw0rd!",
    database=DB_NAME)

# Get a cursor
cursor = cnx.cursor(buffered=True)

# Use 'course_project' database, or create it if 'course_project' database does not already exist.
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
            set_default_values(table_name)
            window['-status-'].update('Database initialized.', visible=True)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                set_default_values(table_name)
            else:
                print("Failed creating table '{}': {}".format(table_name, err))
            
# Clear table and insert default values
def set_default_values(table):
    try:
        cursor.execute("""TRUNCATE TABLE {}""".format(table))
        cursor.execute(DEFAULT_ROWS[table])
        
        # Make sure data is committed to the database
        cnx.commit()
    except mysql.connector.Error as err:
        window['-status-'].update("Failed inserting default values for table '{}': {}".format(table, err))

# Verify row exists within 'user' table
def login(login_event, data):
    valid_inputs = False
    
    valid_inputs = validate_inputs(login_event, data)
    
    if valid_inputs:
        try:
            data_login = (data['-login_username-'], data['-login_password-'])
            cursor.execute("SELECT username, firstName, lastName FROM user WHERE username=%s AND password=%s", data_login)
            if cursor.rowcount == 0:
                window['-login_status-'].update("Failed to log in - incorrect username or password.", visible=True)
            else:
                for (username, fname, lname) in cursor:
                    login_success(username, fname, lname)
        except mysql.connector.Error as err:
            window['-login_status-'].update("Failed to login: {}".format(err), visible=True)
    
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

# Verify login status
def check_login_status():
    if current_user is None:
        window['-current_user-'].update('', visible=False)
    else:
        window['-current_user-'].update('Currently logged in as {}.'.format(current_user), visible=True)

# Clear input fields
def clear_inputs(data):
    for input in data:
        window[input].update('')

# Display Home page
def display_home_page(values):
    check_login_status()
    clear_inputs(values)
    window['-login_status-'].update('', visible=False)
    window['-registration_status-'].update('', visible=False)
    window['-status-'].update('', visible=False)
    window[f'-INITIALIZE-'].update(visible=True)
    window[f'-LOGIN-'].update(visible=False)
    window[f'-REGISTER-'].update(visible=False)

# Display Login page
def display_login_page():
    window['B_LOGIN'].update(visible=True)
    window['B_LOGIN_CANCEL'].update(visible=True)
    window['B_LOGIN_HOME'].update(visible=False)
    window[f'-INITIALIZE-'].update(visible=False)
    window[f'-LOGIN-'].update(visible=True)
    window[f'-REGISTER-'].update(visible=False)
    
# Display Registration page
def display_register_page():
    window['B_REGISTER'].update(visible=True)
    window['B_REGISTER_CANCEL'].update(visible=True)
    window['B_REGISTER_HOME'].update(visible=False)
    window[f'-INITIALIZE-'].update(visible=False)
    window[f'-LOGIN-'].update(visible=False)
    window[f'-REGISTER-'].update(visible=True)

def login_success(userName, firstName, lastName):
    global current_user
    current_user = userName
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
    [sg.Text('', key='-current_user-', visible=False)],
    [sg.Button('Initialize Database', key='B_INIT_DB')],
    [sg.Button(button_text='Login', key='B_INIT_LOGIN'), sg.Button('Register', key='B_INIT_REGISTER')],
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

layout = [
    [
        sg.Column(layout_initialize, key='-INITIALIZE-'),
        sg.Column(layout_register, visible=False, key='-REGISTER-'),
        sg.Column(layout_login, visible=False, key='-LOGIN-')
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
        if event == 'B_INIT_LOGIN': # User clicks 'Login' button
            display_login_page()
        elif event == 'B_INIT_REGISTER': # User clicks 'Register' button
            display_register_page()
        elif event == 'B_LOGIN': # User submits login credentials in 'Login' page
            login(event, values)
        elif event == 'B_REGISTER': # User submits registration credentials in 'Registration' page
            register(event, values)
        elif event == 'B_INIT_DB': # User clicks 'Initialize Database' button
            init_database()
        else: # Default home page
            display_home_page(values)
    
window.close()