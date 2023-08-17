from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.edge import service
from random import *
import os
os.system("cls") #clear screen from previous sessions
import time
import sqlite3
from datetime import datetime, timedelta

options = webdriver.EdgeOptions()
options.use_chromium = True
options.add_argument("start-maximized")
my_service=service.Service(r'msedgedriver.exe')
options.page_load_strategy = 'eager' #do not wait for images to load
options.add_experimental_option("detach", True)
options.add_argument('--no-sandbox')
options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.images": 2 # Setting to disable images
})
#options.add_argument('--disable-dev-shm-usage') # uses disk instead of RAM, may be slow

s = 20 #time to wait for a single component on the page to appear, in seconds; increase it if you get server-side errors «try again later»

driver = webdriver.Edge(service=my_service, options=options)
action = ActionChains(driver)
wait = WebDriverWait(driver,s)

number_of_messages=3
message = []
for i in range(number_of_messages): #the number of messages in the directory
    text_file = open("facebook-message-"+str(i)+".txt", "r")
    message.append(text_file.read())
    text_file.close()

username = "nakigoetenshi@gmail.com"
password = "Super_Mega_Password"
login_page = "https://www.facebook.com/login"
# friend_link = "https://www.facebook.com/atsushi.shigemori.3/" # Japanese
friend_link = "https://www.facebook.com/profile.php?id=100029123601146" # Random China

# Create table to store Facebook pages and dates of sending a message
def create_table():
    conn = sqlite3.connect('users-and-dates.db')
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        facebook_page_url TEXT PRIMARY KEY,
        date_sent TEXT
    )
    """)
    conn.commit()
    conn.close()
create_table()

def send_a_message(driver, anchor_element):
    #store the person's name and attach to the random message to reduce automation detection:
    name = anchor_element.find_element(By.XPATH, './/span[@dir="auto"]').get_attribute('innerHTML')
    personalized_message = "Dear " + name + ",\n\n" + message[randint(0,number_of_messages-1)]
    
    #move to the element and wait for a popup to appear
    action.move_to_element(anchor_element).perform()
    time.sleep(3)   
    
    try:    
        add_friend = driver.find_element(By.XPATH, '//div[@aria-label="Add friend"]')
        action.move_to_element(add_friend).perform()
        action.click(add_friend).perform()
        time.sleep(2)
        try:
            ok_button = driver.find_element(By.XPATH, '//div[@aria-label="OK"]')
            driver.execute_script("arguments[0].click();", ok_button)
            time.sleep(2)
            #move to the element and wait for a popup to appear again:
            action.move_to_element(anchor_element).perform()
            time.sleep(5) 
        except:
            pass
    except:
        pass
    
    message_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@role="dialog"]//div[@aria-label="Message"]')))
    action.click(message_button).perform() 
    time.sleep(5)
    
    send_like = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Send a Like"]')))
    action.move_to_element(send_like).perform()
    action.click(send_like).perform()
    time.sleep(3)
    
    text_area = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Message"]/p')))
    
    lines = personalized_message.split('\n')
    for index, line in enumerate(lines):
        text_area.send_keys(line)
        time.sleep(1)
        if index != len(lines) - 1:  # Check if it's not the last line
            text_area.send_keys(Keys.SHIFT + Keys.ENTER)

    time.sleep(3)
    
    send_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Press Enter to send"]')))
    action.move_to_element(send_button).perform()
    action.click(send_button).perform()
    time.sleep(3)

    sent_or_could_not_send = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="gridcell"]//span[@role="none"]//span[@dir="auto"]'))).get_attribute('innerHTML')
    
    close_chat_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Close chat"]')))
    action.move_to_element(close_chat_button).perform()
    action.click(close_chat_button).perform()
    time.sleep(3)
    
    if "Sent" in sent_or_could_not_send:
        return 0
    else:
        return 1

def check_and_send_message(driver, friend_list_page_element):
    facebook_page_url = friend_list_page_element.get_attribute('href')
    conn = sqlite3.connect('users-and-dates.db')
    cursor = conn.cursor()

    # Query for the user by facebook_page_url
    cursor.execute("SELECT date_sent FROM messages WHERE facebook_page_url = ?", (facebook_page_url,))
    result = cursor.fetchone()

    if result:
        date_sent_str = result[0]
        if date_sent_str:
            date_sent = datetime.strptime(date_sent_str, '%Y-%m-%d')
            if datetime.now() - date_sent > timedelta(days=365):
                if send_a_message(driver, friend_list_page_element) == 0: #if there is a word 'Sent' in the return message
                    update_date_sent(facebook_page_url)
        else:
            if send_a_message(driver, friend_list_page_element) == 0: #if there is a word 'Sent' in the return message
                update_date_sent(facebook_page_url)
    else:
        if send_a_message(driver, friend_list_page_element) == 0: #if there is a word 'Sent' in the return message
            insert_user(facebook_page_url)

    conn.close()

def insert_user(facebook_page_url):
    conn = sqlite3.connect('users-and-dates.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (facebook_page_url, date_sent) VALUES (?, ?)", (facebook_page_url, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()

def update_date_sent(facebook_page_url):
    conn = sqlite3.connect('users-and-dates.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE messages SET date_sent = ? WHERE facebook_page_url = ?", (datetime.now().strftime('%Y-%m-%d'), facebook_page_url))
    conn.commit()
    conn.close()

def login():
    driver.get(login_page)
    time.sleep(3)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="email"]'))).send_keys(username)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="pass"]'))).send_keys(password)
    action.click(wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="loginbutton"]')))).perform()

def scroll_to_bottom(): 
    reached_page_end= False
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    #expand the skills list:
    while not reached_page_end:
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if last_height == new_height:
            reached_page_end = True
        else:
            last_height = new_height

def send_friend_request(driver, anchor_element):
    #move to the element and wait for a popup to appear
    action.move_to_element(anchor_element).perform()
    time.sleep(3)   
    
    try:    
        add_friend = driver.find_element(By.XPATH, '//div[@aria-label="Add friend"]')
        action.move_to_element(add_friend).perform()
        action.click(add_friend).perform()
        time.sleep(2)
        try:
            ok_button = driver.find_element(By.XPATH, '//div[@aria-label="OK"]')
            driver.execute_script("arguments[0].click();", ok_button)
            time.sleep(2)
        except:
            pass
    except:
        pass
       
def main():
    login()
    time.sleep(10)
    if "?id=" in friend_link:
        driver.get(friend_link + "&sk=friends")
    elif friend_link[-1]=="/": # check if there is a slash '/' at the end of the link
        driver.get(friend_link + "friends") 
    else:
        driver.get(friend_link + "/friends") 
    time.sleep(10)
    
    show_page = wait.until(EC.presence_of_element_located((By.XPATH, '//div')))
    action.click(show_page).perform()
    time.sleep(3)
    
    scroll_to_bottom()
    
    # maybe the selector will change 
    # friend_links = driver.find_elements(By.XPATH, '//div[@style="border-radius: max(0px, min(8px, ((100vw - 4px) - 100%) * 9999)) / 8px;"]//a[@role="link" and @tabindex="0"]/span/parent::a')
    friend_elements = driver.find_elements(By.XPATH, '//a[@role="link"]/span[@dir="auto"]/parent::a')
    
    for friend_element in friend_elements:
        try:
            check_and_send_message(driver, friend_element)
            # if You hit the messages limit, comment out the function above and use the one below, to send friend requests without a message:
            # send_friend_request(driver, friend_element)
        except:
            continue

    # Close the only tab, will also close the browser.
    os.system("cls") #clear screen from unnecessary logs since the operation has completed successfully
    print("All Your messages to the friend's pages are sent! \n \nSincerely Yours, \nNAKIGOE.ORG\n")
    driver.close()
    driver.quit()
main()