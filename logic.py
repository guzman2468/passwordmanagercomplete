from PyQt6.QtWidgets import *
from login_window import Ui_MainWindow
from pymongo import MongoClient
import config
from second_window import Ui_SecondWindow
from third_window import Ui_ThirdWindow
import requests


class Database:
    def __init__(self, db_name='password_manager'):
        self.client = MongoClient(config.uri)
        self.db = self.client[db_name]

    def get_collection(self, collection_name='details'):
        return self.db[collection_name]


class SecondWindow(QMainWindow, Ui_SecondWindow):
    def __init__(self, main_window):
        super().__init__()
        self.setupUi(self)
        self.main_window = main_window

        self.add_new_site_button.clicked.connect(self.main_window.add_new)
        self.exit1_button.clicked.connect(self.exit)
        self.search_button.clicked.connect(self.main_window.search_sites)

    def exit(self):
        self.close()
        self.main_window.show()
        self.main_window.first_user_entry.clear()
        self.main_window.first_password_entry.clear()
        self.main_window.status_label.setText('Please create an account or Login')


class ThirdWindow(QMainWindow, Ui_ThirdWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


class Logic(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.collection = self.db.get_collection()
        self.setupUi(self)

        self.acc_create_button.clicked.connect(self.acc_create)
        self.login_button.clicked.connect(self.login)

        self.__first_user_entry = self.first_user_entry
        self.__first_password_entry = self.first_password_entry

    def get_first_user_entry(self):
        return self.__first_user_entry.text().strip()

    def get_first_password_entry(self):
        return self.__first_password_entry.text().strip()

    def acc_create(self):
        '''
        This function handles input validation on the first window by verifying all
        needed inputs are present and meet the minimum length requirements.
        Input validation errors are handled at the caller level, whereas database
        errors are handled at the API level. FULLY FUNCTIONAL AS OF 9/13/2025
        :return: None
        '''
        try:
            if self.get_first_user_entry() == '' or self.get_first_password_entry() == '':
                raise ValueError('All fields must be filled.')
            elif len(self.get_first_user_entry()) < 4 or len(self.get_first_password_entry()) < 4:
                raise ValueError('Username and password must be 4 or more characters long')

            document = {
                "username": self.get_first_user_entry(),
                "password": self.get_first_password_entry(),
                "websites": []
            }

            response = None

            try:
                response = requests.post(f'{config.api_url}/api/accountCreate', json=document)
                response.raise_for_status()
                if response.status_code == 200:
                    self.status_label.setWordWrap(True)
                    self.status_label.setText("Account created! Please login.")
            except requests.exceptions.HTTPError:
                if response is not None:
                    try:
                        error_detail = response.json().get("detail")
                        self.status_label.setWordWrap(True)
                        self.status_label.setText(f'{error_detail}')
                    except ValueError:
                        pass


        except ValueError as e:
            self.status_label.setWordWrap(True)
            self.status_label.setText(str(e))

    def login(self):
        try:
            if self.get_first_user_entry() == '' or self.get_first_password_entry() == '':
                raise ValueError('All fields must be filled.')

            user = self.collection.find_one(
                {"initial_username": self.get_first_user_entry(), "initial_password": self.get_first_password_entry()})

            if user:
                self.open_second_window()
            else:
                raise ValueError("Could not find account with those credentials. Verify all info is typed correctly")

        except ValueError as e:
            self.status_label.setWordWrap(True)
            self.status_label.setText(str(e))

    def open_second_window(self):
        self.second_window = SecondWindow(self)  # Pass the main window to the second window
        pos = self.pos()
        size = self.size()
        self.second_window.setGeometry(pos.x(), pos.y(), size.width(), size.height())
        self.second_window.show()
        self.close()

    def search_sites(self):
        try:
            website_to_find = self.second_window.website_entry.text().lower().strip()
            if website_to_find == '':
                raise ValueError("Search bar must be filled.")

            user_document = self.collection.find_one(
                {"initial_username": self.get_first_user_entry(),
                 "initial_password": self.get_first_password_entry()},
                {"websites": 1}
            )

            if user_document and "websites" in user_document:
                websites_list = user_document["websites"]
                if websites_list:
                    for website in websites_list:
                        name_of_site = website["name"]
                        if website_to_find == name_of_site:
                            user_of_site = website["username"]
                            pass_of_site = website["password"]
                            self.second_window.details_label.setWordWrap(True)
                            self.second_window.details_label.setText(
                                f'Your username for {website_to_find} is: {user_of_site} and your password is: {pass_of_site}'
                            )
                            return

                    self.second_window.details_label.setWordWrap(True)
                    self.second_window.details_label.setText(
                        f'No account details have been added for {website_to_find}.')
                else:
                    self.second_window.details_label.setWordWrap(True)
                    self.second_window.details_label.setText(f'No websites found in your account.')
            else:
                self.second_window.details_label.setWordWrap(True)
                self.second_window.details_label.setText("No websites found in your account.")

        except ValueError as e:
            self.second_window.details_label.setWordWrap(True)
            self.second_window.details_label.setText(str(e))

    def add_new(self):
        self.third_window = ThirdWindow()
        pos = self.second_window.pos()
        size = self.second_window.size()
        self.third_window.setGeometry(pos.x(), pos.y(), size.width(), size.height())
        self.third_window.show()
        self.second_window.close()
        self.third_window.enter_button.clicked.connect(lambda: self.new_website_entry())
        self.third_window.back_button.clicked.connect(lambda: self.back())

    def new_website_entry(self):
        try:
            website_name = self.third_window.website_name_entry.text().lower().strip()
            username = self.third_window.second_username_entry.text()
            password = self.third_window.second_password_entry.text()
            existing_website = self.collection.find_one(
                {"initial_username": self.get_first_user_entry(),
                 "initial_password": self.get_first_password_entry(),
                 "websites.name": website_name})

            if website_name == '' or username == '' or password == '':
                raise ValueError("All fields must be filled")

            elif existing_website:
                self.collection.update_one(
                    {"initial_username": self.get_first_user_entry(),
                     "initial_password": self.get_first_password_entry(),
                     "websites.name": website_name},
                    {"$set": {
                        "websites.$.username": username,
                        "websites.$.password": password
                    }}
                )

            self.collection.update_one(
                {"initial_username": self.get_first_user_entry(), "initial_password": self.get_first_password_entry()},
                {"$push": {
                    "websites": {
                        "name": website_name,
                        "username": username,
                        "password": password
                    }
                }}
            )

            self.third_window.new_website_label.setWordWrap(True)
            self.third_window.new_website_label.setText(
                "Your details have been successfully added. Please enter another or go back."
            )
        except ValueError as e:
            self.third_window.new_website_label.setWordWrap(True)
            self.third_window.new_website_label.setText(str(e))

    def back(self):
        self.open_second_window()
        self.third_window.close()
