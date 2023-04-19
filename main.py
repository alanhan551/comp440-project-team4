import configparser
import mysql.connector
from mysql.connector import errorcode
import PySimpleGUI as sg
from tabulate import tabulate
import datetime
import re
current_user = None
TABLES = {}
ID_STORAGE = []
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
TABLES['review'] = (
    "CREATE TABLE IF NOT EXISTS `review` ("
    "   `id` INT NOT NULL AUTO_INCREMENT,"
    "   `insert_user` varchar(32) NOT NULL,"
    "   `item_id` INT NOT NULL,"
    "   `rating_review` ENUM('Excellent', 'Good', 'Fair', 'Poor') NOT NULL,"
    "   `review_description` varchar(64) NOT NULL,"
    "   `insert_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,"
    "   FOREIGN KEY(`insert_user`) REFERENCES `user`(`username`),"
    "   FOREIGN KEY(`item_id`) REFERENCES `item`(`id`),"
    "   PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB"
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
    "VALUES ('Wireless Earbuds', 'Bluetooth 5.0 Wireless Earbuds', 'Electronics', 70, 'test1'), "
    "       ('Smart Watch', 'Apple Watch Series 6', 'Electronics', 400, 'test2'), "
    "       ('Gaming Console', 'Sony PlayStation 5', 'Electronics', 500, 'test3'), "
    "       ('Crime Fiction Novel', 'Best-selling Crime Fiction Book', 'Books', 15, 'test1'), "
    "       ('Mystery Novel', 'Suspenseful Mystery Book', 'Books', 18, 'test2'), "
    "       ('Science Fiction Novel', 'Imaginative Sci-Fi Book', 'Books', 20, 'test3'), "
    "       ('Sweatshirt', 'Warm Cotton Sweatshirt', 'Clothing', 35, 'test1'), "
    "       ('Jacket', 'Stylish Winter Jacket', 'Clothing', 90, 'test2'), "
    "       ('Boots', 'Waterproof Hiking Boots', 'Clothing', 120, 'test3')"
)


DEFAULT_ROWS['review'] = (
    "INSERT INTO review "
    "(insert_user, item_id, rating_review, review_description) "
    "VALUES ('test1', 1, 'good', 'The new iPhone X is good, but not exceptional')"
)


# Read from server.ini
config = configparser.ConfigParser()
config.read('server.ini')
server_config = config['DEFAULT']
# Connect to server
cnx = mysql.connector.connect(
    host=server_config['Host'],
    port=int(server_config['Port']),
    user=server_config['User'],
    password=server_config['Password'],
    database=server_config['Database'])

# Get a cursor
cursor = cnx.cursor(buffered=True)


# Use 'course_project' database, or create it if 'course_project' database does not already exist.
def init_database():
    try:
        # Initialize 'course_project' database
        cursor.execute("""Use %s""", (server_config['Database'],))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = server_config['Database']
        else:
            window['-status-'].update("Error: {}".format(err), visible=True)
    finally:
        create_tables()


# Create database
def create_database():
    try:
        cursor.execute("""CREATE DATABASE %s DEFAULT CHARACTER SET 'utf8mb4'""", (server_config['Database'],))
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
        # Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        # Truncate the table
        cursor.execute("""TRUNCATE TABLE {}""".format(table))
        # Insert default rows
        cursor.execute(DEFAULT_ROWS[table])
        # Enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        # Commit the changes
        cnx.commit()
    except mysql.connector.Error as err:
        window['-status-'].update("Failed inserting default values for table '{}': {}".format(table, err))


def add_item(item_event, data):
    valid_inputs = False
    valid_inputs = validate_inputs(item_event, data)
    if valid_inputs:
        try:
            valid_user = validate_current_user()
            if valid_user:
                username = window['-current_user-'].get()
                # Check if user has reached daily limit for rows in 'item' table
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM item WHERE insert_user=%s AND insert_date >= CURRENT_DATE() AND insert_date < CURRENT_DATE() + INTERVAL 1 DAY",
                    (username,))
                current_count = 0
                for (count,) in cursor:
                    current_count = count
                if current_count > 2:
                    window['-add_item_status-'].update("Unable to submit - daily item add limit reached for this user.",
                                                       visible=True)
                else:
                    try:
                        data_item = (
                        data['-new_item_title-'], data['-new_item_description-'], data['-new_item_category-'],
                        data['-new_item_price-'], username)
                        cursor.execute(
                            """INSERT INTO item (title, description, category, price, insert_user) VALUES (%s, %s, %s, %s, %s)""",
                            data_item) 

                        cnx.commit()

                        item_add_success()
                    except mysql.connector.Error as err:
                        window['-add_item_status-'].update("Failed to add current item: {}".format(err), visible=True)

            else:
                window['-add_item_status-'].update("No user is currently logged in.", visible=True)
        except mysql.connector.Error as err:
            window['-add_item_status-'].update("Failed to add item: {}".format(err), visible=True)


def search(search_event, data):
    item_titles = []
    if data['-category-']:
        data_entered = ("%" + data['-category-'] + "%",)
        cursor.execute(
            "SELECT id, title, description, category, price FROM item where LENGTH(category)>1 AND category like %s",
            data_entered)
        result = cursor.fetchall()
        output = []
        ID_STORAGE.clear()
        for row in result:
            ID_STORAGE.append(row[0])
            new_price = "${:,.2f}".format(row[4])
            output.append([row[1], row[2], row[3], new_price])
            item_titles.append(row[1])
        table = tabulate(output, headers=["Title                  ", "          Description               ",
                                          "         Category                        ",
                                          "                    Price     "])

        window['-items_dropdown-'].update(values=item_titles)
        window['-TABLE-'].update(table, visible=True)
        
    else:
        window['-TABLE-'].update(data, visible=False)


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
            data_user = (
            data['-register_username-'], data['-register_password-'], data['-fname-'], data['-lname-'], data['-email-'])
            cursor.execute(
                """INSERT INTO user (username, password, firstName, lastName, email) VALUES (%s, %s, %s, %s, %s)""",
                data_user)
            # Make sure data is committed to the database
            cnx.commit()
            register_success()
        except mysql.connector.Error as err:
            window['-status-'].update("Failed to register user: {}".format(err), visible=True)


# Clear input fields
def clear_inputs(data):
    for input in data:
        window[input].update('')


# Display Home page
def display_home_page(values):
    clear_inputs(values)
    window['-add_item_status-'].update('', visible=False)
    window['-login_status-'].update('', visible=False)
    window['-registration_status-'].update('', visible=False)
    window['-status-'].update('', visible=False)
    window[f'-INITIALIZE-'].update(visible=True)
    window[f'-LOGIN-'].update(visible=False)
    window[f'-REGISTER-'].update(visible=False)
    window[f'-ADD_ITEM-'].update(visible=False)
    window[f'-SEARCH-'].update(visible=False)
    window[f'-DISPLAY_REVIEWS-'].update(visible=False)
    window[f'-REVIEW-'].update(visible=False)


# Display Login page
def display_login_page():
    window['B_LOGIN'].update(visible=True)
    window['B_LOGIN_CANCEL'].update(visible=True)
    window['B_LOGIN_HOME'].update(visible=False)
    window[f'-INITIALIZE-'].update(visible=False)
    window[f'-LOGIN-'].update(visible=True)
    window[f'-REGISTER-'].update(visible=False)
    window[f'-ADD_ITEM-'].update(visible=False)
    window[f'-SEARCH-'].update(visible=False)


# Display Registration page
def display_register_page():
    window['B_REGISTER'].update(visible=True)
    window['B_REGISTER_CANCEL'].update(visible=True)
    window['B_REGISTER_HOME'].update(visible=False)
    window[f'-INITIALIZE-'].update(visible=False)
    window[f'-LOGIN-'].update(visible=False)
    window[f'-REGISTER-'].update(visible=True)
    window[f'-ADD_ITEM-'].update(visible=False)
    window[f'-SEARCH-'].update(visible=False)


def display_review_page():
    
    window['-INITIALIZE-'].update(visible=False)
    window['-REGISTER-'].update(visible=False)
    window['-LOGIN-'].update(visible=False)
    window['-ADD_ITEM-'].update(visible=False)
    window['-SEARCH-'].update(visible=False)
    window['-REVIEW-'].update(visible=True)
    window['B_REVIEW_CANCEL'].update(visible=True)


def search_button():
    window['B_SEARCH'].update(visible=True)
    window['B_LOGIN_CANCEL'].update(visible=False)
    window['B_LOGIN_HOME'].update(visible=True)
    window['TABLE'].update(visible=False)


# Display Add Item page
def display_item_add_page():
    window['B_ADD_ITEM'].update(visible=True)
    window['B_ADD_ITEM_CANCEL'].update(visible=True)
    window['B_ADD_ITEM_HOME'].update(visible=False)
    window[f'-INITIALIZE-'].update(visible=False)
    window[f'-LOGIN-'].update(visible=False)
    window[f'-REGISTER-'].update(visible=False)
    window[f'-ADD_ITEM-'].update(visible=True)
    window[f'-SEARCH-'].update(visible=False)


def item_add_success():
    window['-add_item_status-'].update("Item added successfully.", visible=True)
    window['B_ADD_ITEM'].update(visible=False)
    window['B_ADD_ITEM_CANCEL'].update(visible=False)
    window['B_ADD_ITEM_HOME'].update(visible=True)


def register_success():
    window['-registration_status-'].update("Registration successful.", visible=True)
    window['B_REGISTER'].update(visible=False)
    window['B_REGISTER_CANCEL'].update(visible=False)
    window['B_REGISTER_HOME'].update(visible=True)


def validate_current_user():
    return len(window['-current_user-'].get()) > 0


def get_items():
    cursor.execute("""SELECT id, title FROM item""")
    items = cursor.fetchall()
    return items


def display_reviews(item_title):
    items = get_items()
    selected_item_id = next((item[0] for item in items if item[1] == item_title), None)
    
    if selected_item_id:
        try:
            cursor.execute("""SELECT rating_review, review_description, insert_user, insert_date FROM review WHERE item_id = %s ORDER BY insert_date DESC""",
                           (selected_item_id,))
            reviews = cursor.fetchall()
            if not reviews:
                window['-reviews_display-'].update("", visible=True)
                window['-reviews_status-'].update(f"No reviews found for this item '{item_title}'", visible=True)
                
            else:
                formatted_reviews = ""
                i = 1
                for review in reviews:
                    formatted_reviews += f"Review({i}):\n\tUser: {review[2]}\n\tDate: {review[3]}\n\tRating: {review[0]}\n\tDescription: {review[1]}\n\n"
                    i+=1
                window['-reviews_display-'].update(formatted_reviews, visible=True)
                window['-reviews_status-'].update("", visible=False)
        except mysql.connector.Error as err:
            window["-reviews_status-"].update(f"Failed to fetch reviews: {err}", visible=True)
            
    else:
        if(item_title==""):
            window["-reviews_status-"].update(f"No item Selected ", visible=True)
        else:
            window["-reviews_status-"].update(f"No item found with name '{item_title}'", visible=True)


def display_show_reviews_page():
    items = get_items()
    item_titles = [item[1] for item in items]
    window['-items_dropdown_reviews-'].update(values=item_titles)
    window['-INITIALIZE-'].update(visible=False)
    window['-DISPLAY_REVIEWS-'].update(visible=True)


# Validate inputs
def validate_inputs(event, data):
    if event == 'B_ADD_ITEM':
        for input in ('-new_item_title-', '-new_item_description-', '-new_item_category-', '-new_item_price-'):
            if (len(data[input]) == 0):
                window['-add_item_status-'].update('Field(s) cannot be left blank.', visible=True)
                return False
            elif (input == '-new_item_title-' and len(data[input]) > 32):
                window['-add_item_status-'].update('Title cannot exceed 32 characters.', visible=True)
                return False
            elif (input == '-new_item_description-' and len(data[input]) > 64):
                window['-add_item_status-'].update('Description cannot exceed 64 characters.', visible=True)
                return False
            elif (input == '-new_item_category-' and len(data[input]) > 255):
                window['-add_item_status-'].update('Category cannot exceed 255 characters.', visible=True)
                return False
            elif (input == '-new_item_price-' and validate_price(data[input]) is False):
                window['-add_item_status-'].update('Price must be in proper format.', visible=True)
                return False
    elif event == 'B_LOGIN':
        for input in ('-login_username-', '-login_password-'):
            if len(data[input]) == 0:
                window['-login_status-'].update('Field(s) cannot be left blank.', visible=True)
                return False
            elif len(data[input]) > 32:
                window['-login_status-'].update('Field cannot exceed 32 characters.', visible=True)
                return False
    else:
        for input in (
        '-register_username-', '-register_password-', '-register_password2-', '-fname-', '-lname-', '-email-'):
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


# Validate price
def validate_price(price):
    isValid = True
    priceRegex = re.compile(r'^-?(0|[1-9][0-9]*)?(\.\d{1,2})?$')
    matchedObject = priceRegex.search(price)
    if matchedObject is None:
        isValid = False
    return isValid


# Validate username
def validate_username(username):
    isValid = True
    try:
        # Check if any rows in 'user' table contain user inputted username
        cursor.execute("""SELECT COUNT(*) AS count FROM user WHERE username=%s""", (username,))
        for (count,) in cursor:
            if count > 0:
                window['-registration_status-'].update("Username '{}' is already in use.".format(username),
                                                       visible=True)
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


def login(login_event, data):
    valid_inputs = False
    valid_inputs = validate_inputs(login_event, data)

    if valid_inputs:
        try:
            data_login = (data['-login_username-'], data['-login_password-'])
            cursor.execute("SELECT username, firstName, lastName FROM user WHERE username=%s AND password=%s",
                           data_login)
            if cursor.rowcount == 0:
                window['-login_status-'].update("Failed to log in - incorrect username or password.", visible=True)
            else:
                for (username, fname, lname) in cursor:
                    login_success(username, fname, lname)
        except mysql.connector.Error as err:
            window['-login_status-'].update("Failed to login: {}".format(err), visible=True)

def login_success(userName, firstName, lastName):
    global current_user
    current_user = {
        'username': userName,
        'fname': firstName,
        'lname': lastName
    } 
    window['-login_status_text-'].update("Currently logged in as", visible=True)
    window['-current_user-'].update(userName, visible=True)
    window['-login_status-'].update("Successfully logged in. Welcome back, {} {}!".format(firstName, lastName),
                                    visible=True)
    window['B_INIT_ADD_ITEM'].update(visible=True)
    window['B_INIT_SHOW_REVIEWS'].update(visible=True)
    window['B_LOGIN'].update(visible=False)
    window['B_LOGIN_CANCEL'].update(visible=False)
    window['B_LOGIN_HOME'].update(visible=True)
    window['B_SEARCH'].update(visible=True)


def submit_review(item_event, data):
    try:
        valid_user = validate_current_user()
        if valid_user:
            username = window['-current_user-'].get()
        
            items = get_items()
            selected_item_title = values["-items_dropdown-"]
            selected_item_id = next((item[0] for item in items if item[1] == selected_item_title), None)
            rating = values["-rating_dropdown-"]
            review_description = values["-review_description-"]
            
            # Check the review_description is within 64 character
            if(len(review_description)>64):
                window["-review_status-"].update("Description cannot have more than 64 characters!", visible=True)
                window.refresh()
            else:
                cursor.execute("""SELECT insert_user FROM item WHERE id = %s""", (selected_item_id,))
                item_owner_id = cursor.fetchone()
                if item_owner_id and item_owner_id[0] == username:
                    window["-review_status-"].update("You cannot review your own item.", visible=True)
                else:
                    # Check if the user has already submitted 3 reviews today

                    try:

                        cursor.execute("""
                                                     SELECT COUNT(*) FROM review 
                                                     WHERE insert_user = %s AND insert_date >= CURRENT_DATE() AND insert_date < CURRENT_DATE() + INTERVAL 1 DAY
                                                     """, (username,))
                        daily_review_count = cursor.fetchone()[0]
                    except mysql.connector.Error as err:
                        daily_review_count = 0

                    if daily_review_count >= 3:
                        window["-review_status-"].update("You have reached the maximum limit of 3 reviews per day.", visible=True)
                        window.refresh()
                    else:
                        try:
                            cursor.execute(
                                """INSERT INTO review (insert_user, item_id, rating_review, review_description, insert_date) VALUES (%s, %s, %s, %s, NOW())""",
                                (username, selected_item_id, rating, review_description))
                            cnx.commit()
                            window["-review_status-"].update("Review submitted successfully.", visible=True)
                            window.refresh()
                        except mysql.connector.Error as err:
                            window["-review_status-"].update(f"Failed to submit review: {err}", visible=True)
        else:
            window["-review_status-"].update("No user is currently logged in.", visible=True)
            window.refresh()
    except mysql.connector.Error as err:
        window["-review_status-"].update("Failed to submit review: {}".format(err), visible=True)
        window.refresh()

sg.theme('DarkAmber')  # Add a theme of color
sg.set_options(font=('Arial', 24))
# All the stuff inside the window

layout_initialize = [
    [sg.Text('', key='-login_status_text-', visible=False), sg.Text('', key='-current_user-', visible=False)],
    [sg.Button('Initialize Database', key='B_INIT_DB')],
    [sg.Button(button_text='Login', key='B_INIT_LOGIN'), sg.Button('Register', key='B_INIT_REGISTER')],
    [sg.Button(button_text='Add Item', visible=False, key='B_INIT_ADD_ITEM')],
    [sg.Button(button_text='Show Reviews', visible=False, key='B_INIT_SHOW_REVIEWS')],
    [sg.Button(button_text='Search', visible=False, key='B_SEARCH')],
    [sg.Text('', key='-status-', visible=False)]
]

layout_item_add = [
    [sg.Text('Title'), sg.InputText(key='-new_item_title-')],
    [sg.Text('Description'), sg.InputText(key='-new_item_description-')],
    [sg.Text('Category'), sg.InputText(key='-new_item_category-')],
    [sg.Text('Price'), sg.InputText(key='-new_item_price-')],
    [sg.Button(button_text='Submit', key='B_ADD_ITEM'), sg.Button('Cancel', key='B_ADD_ITEM_CANCEL'),
     sg.Button('Home', key='B_ADD_ITEM_HOME', visible=False)],
    [sg.Text('', key='-add_item_status-', visible=False)]
]

layout_login = [
    [sg.Text('Username'), sg.InputText(size=(32, 1), key='-login_username-')],
    [sg.Text('Password'), sg.InputText(size=(32, 1), key='-login_password-')],
    [sg.Button(button_text='Submit', key='B_LOGIN'), sg.Button('Cancel', key='B_LOGIN_CANCEL'),
     sg.Button('Home', key='B_LOGIN_HOME', visible=False)],
    [sg.Text('', key='-login_status-', visible=False)]
]

layout_search = [
    [sg.Text('Search by Category'), sg.InputText(key='-category-')],
    [sg.Button(button_text='Search', key='B_SEARCH_2'), sg.Button('Cancel', key='B_SEARCH_CANCEL'),sg.Button(button_text='Write a Review', key='B_INIT_REVIEW')],
    [sg.Text(key="-TABLE-")],
    [sg.Text("Select Item"), sg.Combo(["******************"], key="-items_dropdown-", readonly=True)],
    [sg.Text("Rating"), sg.Combo(["Excellent", "Good", "Fair", "Poor"], key="-rating_dropdown-", readonly=True)],
    [sg.Text("Description"), sg.InputText(key="-review_description-")],
    [sg.Button("Submit", key="B_REVIEW_SUBMIT"), sg.Button("Home", key="B_REVIEW_CANCEL")],
    [sg.Text("", key="-review_status-", visible=False)]
]

layout_register = [
    [sg.Text('Username'), sg.InputText(size=(32, 1), key='-register_username-')],
    [sg.Text('Password'), sg.InputText(size=(32, 1), key='-register_password-')],
    [sg.Text('Re-enter password'), sg.InputText(size=(32, 1), key='-register_password2-')],
    [sg.Text('First Name'), sg.InputText(size=(32, 1), key='-fname-')],
    [sg.Text('Last Name'), sg.InputText(size=(32, 1), key='-lname-')],
    [sg.Text('E-mail'), sg.InputText(key='-email-')],
    [sg.Button(button_text='Submit', key='B_REGISTER'), sg.Button('Cancel', key='B_REGISTER_CANCEL'),
     sg.Button('Home', key='B_REGISTER_HOME', visible=False)],
  
    [sg.Text('', key='-registration_status-', visible=False)]
]

# Extract item titles from the items list
layout_review = [
    [sg.Text("Select Item"), sg.Combo(["******************"], key="-items_dropdown-", readonly=True)],
    [sg.Text("Rating"), sg.Combo(["Excellent", "Good", "Fair", "Poor"], key="-rating_dropdown-", readonly=True)],
    [sg.Text("Description"), sg.InputText(key="-review_description-")],
    [sg.Button("Submit", key="B_REVIEW_SUBMIT"), sg.Button("Home", key="B_REVIEW_CANCEL")],
    [sg.Text("", key="-review_status-", visible=False)]
]

layout_display_reviews = [
    [sg.Text("Select Item"), sg.Combo(["******************"], key="-items_dropdown_reviews-", readonly=True)],
    [sg.Button("Show Reviews", key="B_SHOW_REVIEWS"), sg.Button("Home", key="B_SHOW_REVIEWS_CANCEL"),
     sg.Button("Home", key="B_SHOW_REVIEWS_HOME", visible=False)],
    [sg.Text("", key="-reviews_status-", visible=False)],
    [sg.Multiline(size=(60, 15), key="-reviews_display-", disabled=True, visible=False)],
]

layout = [
    [
        sg.Column(layout_initialize, key='-INITIALIZE-'),
        sg.Column(layout_register, visible=False, key='-REGISTER-'),
        sg.Column(layout_login, visible=False, key='-LOGIN-'),
        sg.Column(layout_item_add, visible=False, key='-ADD_ITEM-'),
        sg.Column(layout_search, visible=False, key='-SEARCH-'),
        sg.Column(layout_review, visible=False, key="-REVIEW-"),
        sg.Column(layout_display_reviews, visible=False, key="-DISPLAY_REVIEWS-")
    ]
]

# Create the Window
window = sg.Window('COMP 440 Course Project', layout)

# Event loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:  # if user closes window
        cursor.close()
        cnx.close()
        break
    else:
        if event == 'B_INIT_LOGIN':  # User clicks 'Login' button
            display_login_page()
        elif event == 'B_INIT_REGISTER':  # User clicks 'Register' button
            display_register_page()
        elif event == 'B_INIT_ADD_ITEM':  # User clicks 'Add Item' button
            display_item_add_page()
        elif event == 'B_LOGIN':  # User submits login credentials in 'Login' page
            login(event, values)
        elif event == 'B_REGISTER':  # User submits registration credentials in 'Registration' page
            register(event, values)
        elif event == 'B_ADD_ITEM':
            add_item(event, values)
        elif event == 'B_INIT_DB':  # User clicks 'Initialize Database' button
            init_database()
        elif event == 'B_SEARCH':  # User enters text to search
            window[f'-INITIALIZE-'].update(visible=False)
            window[f'-LOGIN-'].update(visible=False)
            window[f'-REGISTER-'].update(visible=False)
            window[f'-SEARCH-'].update(visible=True)
            window[f'B_INIT_REVIEW'].update(visible=False)
            window[f'-TABLE-'].update(visible=False)
        elif event == 'B_SEARCH_2':
            search(event, values)
        elif event == 'B_INIT_REVIEW':  # User clicks 'Write a Review' button
            display_review_page()
        elif event == 'B_REVIEW_SUBMIT':
            submit_review(event,values)
            window.refresh()
        elif event == 'B_INIT_SHOW_REVIEWS':  # User clicks 'Show Reviews' button
            display_show_reviews_page()
        elif event == 'B_SHOW_REVIEWS':  # User selects an item and clicks 'Show Reviews'
            display_reviews(values['-items_dropdown_reviews-'])
        else:  # Default home page
            display_home_page(values)

window.close()
