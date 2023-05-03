import configparser
import mysql.connector
from mysql.connector import errorcode
import PySimpleGUI as sg
from tabulate import tabulate
import re

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

TABLES['favorite_seller'] = (
    "CREATE TABLE IF NOT EXISTS `favorite_seller` ("
    "   `id` INT NOT NULL AUTO_INCREMENT,"
    "   `f_username` varchar(32) NOT NULL,"
    "   `fav_user` varchar(32) NOT NULL,"
    "   FOREIGN KEY(`f_username`) REFERENCES `user`(`username`),"
    "   FOREIGN KEY(`fav_user`) REFERENCES `user`(`username`),"
    "   PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
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
    "VALUES ('test1', 2, 'Good', 'The new iPhone X is good, but not exceptional'), "
    "       ('test1', 3, 'Excellent', 'Very nostalgic, loved to play it.'), "
    "       ('test1', 5, 'Poor', 'Not really into mystery novels.'), "
    "       ('test2', 1, 'Excellent', 'Great for music during exercise.'), "
    "       ('test3', 4, 'Good', 'Suspenseful and catchy')"
)

DEFAULT_ROWS['favorite_seller'] = (
    "INSERT INTO favorite_seller "
    "(f_username, fav_user) "
    "VALUES ('test1', 'test2'), "
    "       ('test2', 'test3'), "
    "       ('test3', 'test1'), "
    "       ('test4', 'test5'), "
    "       ('test5', 'test2')  "
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

def display_queries():

    query = '''SELECT insert_user, COUNT(*) as num_items
    FROM item
    WHERE insert_date >= '2020-05-01'
    GROUP BY insert_user
    HAVING COUNT(*) >= (
        SELECT COUNT(*) as num_items
        FROM item
        WHERE insert_date >= '2020-05-01'
        GROUP BY insert_user
        ORDER BY num_items DESC
        LIMIT 1
)'''
    cursor.execute(query)
    result4 = cursor.fetchall()
    new_string4 = []
    for row in result4:
        new_string4.append(row[0])
    if len(new_string4) == 0:
        new_string4 = "No results found!"
    window['-queries_result4-'].update(new_string4, visible=True)
    
    cursor.execute(" SELECT distinct user.username FROM user  LEFT JOIN item ON item.insert_user = user.username LEFT JOIN review ON review.item_id = item.id GROUP BY user.username, item.id HAVING COUNT(CASE WHEN review.rating_review = 'Excellent' THEN 1 END) < 3 OR COUNT(review.rating_review) IS NULL")
    result6 = cursor.fetchall()
    new_string6 = []
    for i in result6:
        new_string6.append(i[0])
    if len(new_string6) == 0:
        new_string6 = "No results found!"
    window['-queries_result6-'].update(new_string6, visible=True)
    
    cursor.execute("SELECT DISTINCT r.insert_user FROM review r WHERE NOT EXISTS (SELECT * FROM review WHERE insert_user=r.insert_user AND rating_review='Poor')")
    result7 = cursor.fetchall()
    new_string7 = []
    for i in result7:
        new_string7.append(i[0])
    if len(new_string7) == 0:
        new_string7 = "No results found!"
    window['-queries_result7-'].update(new_string7, visible=True)
    
    query = '''SELECT DISTINCT u.username 
    FROM user u 
    JOIN review r ON u.username = r.insert_user 
    WHERE r.rating_review = 'Poor' 
    AND NOT EXISTS (
        SELECT 1 
        FROM review r2 
        WHERE r2.insert_user = u.username 
        AND r2.rating_review != 'Poor'
    )'''
    cursor.execute(query)
    result8 = cursor.fetchall()
    new_string8 = []
    for row in result8:
        new_string8.append(row[0])
    if len(new_string8) == 0:
        new_string8 = "No results found!"
    window['-queries_result8-'].update(new_string8, visible=True)
    
    query = '''SELECT DISTINCT u.username, u.firstName, u.lastName
            FROM user u
            INNER JOIN item i ON u.username = i.insert_user
            LEFT JOIN (
                SELECT item_id
                FROM review
                WHERE rating_review = 'Poor'
            ) r ON i.id = r.item_id
            WHERE r.item_id IS NULL
            OR i.id NOT IN (
                SELECT item_id
                FROM review
            )'''
    cursor.execute(query)
    result9 = cursor.fetchall()
    new_string9 = []
    for row in result9:
        new_string9.append(row[0])
    if len(new_string9) == 0:
        new_string9 = "No results found!"
    window['-queries_result9-'].update(new_string9, visible=True)
    
    query = '''SELECT DISTINCT r1.insert_user as user_a, r2.insert_user as user_b
                FROM review r1
                JOIN review r2 ON r1.item_id = r2.item_id AND r1.insert_user <> r2.insert_user
                WHERE r1.rating_review = 'excellent' AND r2.rating_review = 'excellent'
                AND NOT EXISTS (
                  SELECT *
                  FROM review r3
                  WHERE r3.item_id = r1.item_id
                  AND ((r3.insert_user = r1.insert_user AND r3.rating_review != 'excellent')
                       OR (r3.insert_user = r2.insert_user AND r3.rating_review != 'excellent'))
                )'''
                
    cursor.execute(query)
    result10 = cursor.fetchall()
    new_string10 = []
    for row in result10:
        new_string10.append(row[0])
    if len(new_string10) == 0:
        new_string10 = "No results found!"
    window['-queries_result10-'].update(new_string10, visible=True)
    

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
    window['B_QUERIES'].update(visible=True)
    window['B_QUERY_CANCEL'].update(visible=False)
    window[f'-DISPLAY_QUERIES-'].update(visible=False)
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
    window['B_QUERIES'].update(visible=False)

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
    window['B_QUERIES'].update(visible=False)

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

def display_queries_page():
    window[f'-DISPLAY_QUERIES-'].update(visible=True)
    window[f'-INITIALIZE-'].update(visible=False)
    window[f'-LOGIN-'].update(visible=False)
    window[f'-REGISTER-'].update(visible=False)
    window[f'-SEARCH-'].update(visible=False)
    window[f'B_INIT_REVIEW'].update(visible=False)
    window[f'-TABLE-'].update(visible=False)
    window['B_QUERY_CANCEL'].update(visible=True)
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
    [sg.Button(button_text='Queries', visible=True, key='B_QUERIES')],
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
    
layout_display_queries = [
    [sg.Text("Query Results")],
    [sg.Text("Users who posted most number of items ", key="-query4-", visible=True)],
    [sg.Text("  ", key="-queries_result4-", visible=True)],    
    [sg.Text("Users who never posted an excellent item ", key="-query6-", visible=True)],
    [sg.Text("  ", key="-queries_result6-", visible=True)],
    [sg.Text("Users who never posted poor review", key="-query7-", visible=True)],
    [sg.Text("  ", key="-queries_result7-", visible=True)],
    [sg.Text("Users who posted review but each of them is poor", key="-query8-", visible=True)],
    [sg.Text("  ", key="-queries_result8-", visible=True)],
    [sg.Text("Users who never get a Poor review ", key="-query9-", visible=True)],
    [sg.Text("  ", key="-queries_result9-", visible=True)],
    [sg.Text("User pairs who always give each other excellent review ", key="-query10-", visible=True)],
    [sg.Text("  ", key="-queries_result10-", visible=True)],
    [sg.Button('Home', key="B_QUERY_CANCEL")],
]

layout = [
    [
        sg.Column(layout_initialize, key='-INITIALIZE-'),
        sg.Column(layout_register, visible=False, key='-REGISTER-'),
        sg.Column(layout_login, visible=False, key='-LOGIN-'),
        sg.Column(layout_item_add, visible=False, key='-ADD_ITEM-'),
        sg.Column(layout_search, visible=False, key='-SEARCH-'),
        sg.Column(layout_review, visible=False, key="-REVIEW-"),
        sg.Column(layout_display_reviews, visible=False, key="-DISPLAY_REVIEWS-"),
        sg.Column(layout_display_queries, visible= False, key="-DISPLAY_QUERIES-")
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
        elif event == 'B_QUERIES':
            display_queries_page()
            display_queries()
        else:  # Default home page
            display_home_page(values)

window.close()