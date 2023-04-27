from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import StaleElementReferenceException
import time
import os
import json
import requests
from mimetypes import guess_extension
from threading import Thread
import pathlib
from Config import (scrape_content_type,
                    city,
                    download_images,
                    headless_mode,
                    keep_driver_cache,
                    disable_loading_images,
                    delay_between_requests)
import logging
# from playsound import playsound


fixed_error_message = ' Correct it in the Config.py file.'
assert scrape_content_type in ['car', 'realestate'], 'Currently supported advertisements type: car - realestate.' + fixed_error_message
assert city in ['tehran'], 'Currently supported cities: tehran.' + fixed_error_message
assert isinstance(download_images, bool), 'download_images must be a bool.' + fixed_error_message
assert isinstance(headless_mode, bool), 'headless_mode must be a bool.' + fixed_error_message
assert isinstance(keep_driver_cache, bool), 'keep_driver_cache must be a bool.' + fixed_error_message
assert isinstance(disable_loading_images, bool), 'disable_loading_images must be a bool.' + fixed_error_message
assert isinstance(delay_between_requests, (int, float)), 'delay_between_requests must be int or float.' + fixed_error_message

scrape_content_type = scrape_content_type.capitalize()
city = city.capitalize()
working_dir = str(pathlib.Path(__file__).parent.resolve()) + '/Extracted Advertisements'
for i in range(4):
    try:
        if i == 0:
            os.mkdir('{}'.format(working_dir))
        elif i == 1:
            os.mkdir('{}/{}'.format(working_dir, scrape_content_type))
        elif i == 2:
            os.mkdir('{}/{}/{}'.format(working_dir,
                                       scrape_content_type, 
                                       city))
        elif i == 3:
            os.mkdir('{}/{}/{}'.format(working_dir,
                                       scrape_content_type, 
                                       city))
    except:
        pass
logging.basicConfig(
    format="%(asctime)s - %(levelname)s:  %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)
# service = Service(ChromeDriverManager().install())
service = Service(executable_path=working_dir.replace('/Extracted Advertisements', '') + '/chromedriver')
options = webdriver.ChromeOptions()
caps = DesiredCapabilities().CHROME
caps["pageLoadStrategy"] = "eager"
if keep_driver_cache:
    options.add_argument(f"user-data-dir={working_dir.replace('/Extracted Advertisements', '')}/Cache")
if disable_loading_images:
    options.add_argument('--blink-settings=imagesEnabled=false')
if headless_mode:
    options.add_argument('--headless')
if not headless_mode:
    options.add_argument('--start-maximized')
driver = webdriver.Chrome(service=service, options=options, desired_capabilities=caps)
actions = ActionChains(driver)
driver.get(f"""https://divar.ir/s/{city.lower()}/{'auto' if scrape_content_type.lower() == 'car' else 'real-estate' if scrape_content_type.lower() == 'realestate' else None}""")
WebDriverWait(driver, 120).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
logging.info('The Divaar\'s main page has been fetched completely.')
last_request = time.time()
wait_element = WebDriverWait(driver, 10)
item_number = 0
def async_downloader(image_urls):
    threads = list()
    def download_thread(image_url, image_index):
        for i in range(3):
            try:
                respond = requests.get(image_url, timeout=5)
                open(f'{working_dir}/{scrape_content_type}/{city}/{item_number}/picture_{image_index}{guess_extension(respond.headers["content-type"])}', 'wb').write(respond.content)
            except:
                logging.critical(f'{"[Oops] " if i == 2 else ""}Could not get {image_index}th image. Try Number: {i + 1} / 3.')
                time.sleep(0.5)
            else:
                logging.info(f'[OK] Downloading the {image_index + 1}th image out of {len(image_urls)} image(s) finished: {image_url}')
                break
    for image_index, image_url in enumerate(image_urls):
        threads.append(Thread(target=download_thread, args=(image_url, image_index)))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


while True:
    try:
        try_again_button = driver.find_element(By.XPATH, '//*[text()="تلاش دوباره"]/parent::*')
    except:
        pass
    else:
        try_again_button.click()
    try:
        refresh_elements = False
        try:
            current_elements = driver.find_elements(By.XPATH, '//*[@class="post-card-item-af972 kt-col-6-bee95 kt-col-xxl-4-e9d46" and not(@processed="true")]')
        except:
            # playsound('./1.mp3')
            # driver.execute_script("""window.scrollBy(0, -200)""")
            # time.sleep(1)
            driver.execute_script("""window.scrollBy(0, 200)""")
            continue
        for element in current_elements:
            attr = element.get_attribute('class')
            driver.execute_script(f"""document.querySelectorAll('.post-card-item-af972.kt-col-6-bee95.kt-col-xxl-4-e9d46').forEach((element) => element.setAttribute('processed', 'true'))""")
        while True:
            handle_counter = 0
            while handle_counter < 3:
                try:
                    current_element = current_elements[handle_counter]
                except IndexError:
                    refresh_elements = True
                    handle_counter = 0
                    break
                driver.switch_to.window(driver.window_handles[0])
                try:
                    while time.time() - last_request < delay_between_requests:
                        time.sleep(0.001)
                        pass
                    last_request = time.time()
                    actions.key_down(Keys.CONTROL).click(current_element).perform()
                except StaleElementReferenceException as e:
                    logging.critical(e)
                    pass
                current_handles = driver.window_handles
                current_elements.pop(0)
                handle_counter = handle_counter + 1
            if refresh_elements:
                driver.switch_to.window(driver.window_handles[0])
                # playsound('./2.mp3')
                # driver.execute_script("""window.scrollBy(0, -200)""")
                # time.sleep(1)
                driver.execute_script("""window.scrollBy(0, 200)""")
                break
            for index, handle in enumerate(current_handles):
                if index > 0:
                    print("-" * 50)
                    logging.info(f'[...] Processing the {item_number}th {scrape_content_type} advertisement in {city.capitalize()}')
                    driver.switch_to.window(handle)
                    # Checking if the page is a valid page to scrape.
                    try:
                        wait_element.until(EC.visibility_of_element_located((By.XPATH, '//*[@class="kt-page-title__title kt-page-title__title--responsive-sized"]')))
                        # driver.find_element(By.XPATH, '//*[@class="kt-page-title__title kt-page-title__title--responsive-sized"]')
                    except:
                        logging.critical(f'{driver.current_url} did not load properly. Ignoring...')
                        driver.close()
                        continue
                    else:
                        driver.execute_script("window.stop()")
                        pass
                    current_item_data = dict()
                    current_item_data['Title'] = driver.find_element(By.XPATH, '//*[@class="kt-page-title__title kt-page-title__title--responsive-sized"]').text
                    current_item_data['Explanations'] = driver.find_element(By.XPATH, '//p[@class="kt-description-row__text kt-description-row__text--primary"]').text
                    current_item_data['LocationCity'] = city
                    current_item_data['LocationExact'] = '،'.join(driver.find_element(By.XPATH, '//*[@class="kt-page-title__subtitle kt-page-title__subtitle--responsive-sized"]').text.split('،')[1:]).strip()
                    current_item_data['FetchTimeInEpoch'] = time.time()
                    current_item_data['PostTimeRelatedToFetchTime'] = driver.find_element(By.XPATH, '//*[@class="kt-page-title__subtitle kt-page-title__subtitle--responsive-sized"]').text.split('،')[0].split('در')[0].strip()
                    current_item_data['Tags'] = [element.text for element in driver.find_elements(By.XPATH, '//*[@class="kt-wrapper-row"]//a//button')]
                    current_item_data['URL'] = driver.current_url
                    if scrape_content_type.lower() == 'car':
                        elements_data_1 = {
                            'Color': 'رنگ',
                            'YearOfConstruction': 'مدل (سال تولید)',
                            'LifeSpan': 'کارکرد',
                        }
                        for key, value in elements_data_1.items():
                            try:
                                current_item_data[key] = driver.find_element(By.XPATH, f'//span[@class="kt-group-row-item__title kt-body kt-body--sm" and contains(text(), "{value}")]/following-sibling::span[@class="kt-group-row-item__value"]').text
                            except:
                                pass
                        elements_data_2 = {
                            'Fuel': 'نوع سوخت',
                            'EngineCondition': 'وضعیت موتور',
                            'ChassisCondition': 'وضعیت شاسی‌ها',
                            'BodyCondition': 'وضعیت بدنه',
                            'InsuranceDeadline': 'مهلت بیمهٔ شخص ثالث',
                            'Gearbox': 'گیربکس',
                            'Price': 'قیمت فروش نقدی'
                        }
                        for key, value in elements_data_2.items():
                            try:
                                current_item_data[key] = driver.find_element(By.XPATH, f'//p[@class="kt-base-row__title kt-unexpandable-row__title" and contains(text(), "{value}")]/parent::*/following-sibling::*/p[@class="kt-unexpandable-row__value"]').text
                            except:
                                pass
                                
                        try:
                            current_item_data['Brand'] = driver.find_element(By.XPATH, f'//p[@class="kt-base-row__title kt-unexpandable-row__title" and text()="برند و تیپ"]/parent::*/parent::*//*[@class="kt-unexpandable-row__action kt-text-truncate"]').text
                        except:
                            pass
                        
                        try:
                            driver.find_element(By.XPATH, '//*[@class="kt-title-row__title" and text()="فروش اقساطی"]')
                        except:
                            pass
                        else:
                            installment_information = dict()
                            elements_data_3 = {
                                'MinimumPrepaidAmount': 'حداقل مبلغ پیش‌پرداخت',
                                'AmountOfEachInstallment': 'مبلغ هر قسط',
                                'NumberOfInstallments': 'تعداد اقساط'
                            }
                            current_item_data['InstallmentInformation'] = installment_information
                            for key, value in elements_data_3.items():
                                try:
                                    installment_information[key] = driver.find_element(By.XPATH, f'//p[@class="kt-base-row__title kt-unexpandable-row__title" and contains(text(), "{value}")]/parent::*/following-sibling::*/p[@class="kt-unexpandable-row__value"]').text
                                except:
                                    pass
                    elif scrape_content_type.lower() == 'realestate':
                        elements_data_1 = {
                            'Meterage': 'متراژ',
                            'YearOfConstruction': 'ساخت',
                            'RoomsCount': 'اتاق',
                            'Deposit': 'ودیعه',
                            'MonthlyRent': 'اجارهٔ ماهانه'
                        }
                        for key, value in elements_data_1.items():
                            try:
                                current_item_data[key] = driver.find_element(By.XPATH, f'//span[@class="kt-group-row-item__title kt-body kt-body--sm" and contains(text(), "{value}")]/following-sibling::span[@class="kt-group-row-item__value"]').text
                            except:
                                pass
                        elements_data_2 = {
                            'TotalPrice': 'قیمت کل',
                            'PricePerMeter': 'قیمت هر متر',
                            'Floor': 'طبقه',
                            'Deposit': 'ودیعه',
                            'MonthlyRent': 'اجارهٔ ماهانه'
                        }
                        for key, value in elements_data_2.items():
                            try:
                                current_item_data[key] = driver.find_element(By.XPATH, f'//p[@class="kt-base-row__title kt-unexpandable-row__title" and contains(text(), "{value}")]/parent::*/following-sibling::*/p[@class="kt-unexpandable-row__value"]').text
                            except:
                                pass
                                
                        try:
                            current_item_data['RealEstateAgency'] = driver.find_element(By.XPATH, f'//p[@class="kt-base-row__title kt-unexpandable-row__title" and text()="آژانس املاک"]/parent::*/parent::*//*[@class="kt-unexpandable-row__action kt-text-truncate"]').text
                        except:
                            pass
                        elements_data_3 = {
                            'Elevator': 'آسانسور',
                            'Warehouse': 'انباری',
                            'Parking': 'پارکینگ',
                        }
                        for key, value in elements_data_3.items():
                            try:
                                current_item_data[key] = False if 'ندارد' in driver.find_element(By.XPATH, f'//*[@class="kt-group-row-item__value kt-body kt-body--stable" and contains(text(), "{value}")]').text else True
                            except:
                                print('this is the error', e)
                                pass
                    if download_images:
                        try:
                            os.mkdir(f'{working_dir}/{scrape_content_type}/{city}/{item_number}')
                        except:
                            pass
                    json_data_location = f'{working_dir}/{scrape_content_type}/{city}/{item_number}/data.json' if download_images else f'{working_dir}/{scrape_content_type}/{city}/{item_number}.json'
                    with open(json_data_location, 'w') as f:
                        json.dump(current_item_data, f, ensure_ascii=False, indent=4, separators=(',', ': '))
                    if download_images:
                        image_urls = [image_element.get_attribute('srcset').split('?')[0] for image_element  in driver.find_elements(By.XPATH, '//*[@class="kt-carousel__slide-wrapper"]//button//*[@class="kt-image-block__image kt-image-block__image--fading"]//preceding-sibling::source')]
                        async_downloader(image_urls)
                    item_number += 1
                    driver.close()
                # actions.key_down(Keys.CONTROL).send_keys('w').perform()
    except Exception as e:
        logging.critical(e)
        pass