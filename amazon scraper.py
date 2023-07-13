import lxml
from bs4 import BeautifulSoup
import bs4
import time
import pandas
from undetected_chromedriver import Chrome, ChromeOptions
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class AmazonScraper:
    def __init__(self,base_url,search_query,price_range):
        self.base_url = base_url
        self.search_query = search_query
        self.last_query_time = 0
        self.price_range = price_range

        q = self.search_query.split(" ")
        if len(q)>1:
            q = "_".join(q)
        else:
            q = q[0]
        self.excel_name = (f"{q}.xlsx")

        self.data = []
        self.invalid_links_data = []
        self.keywords = set()
        option = ChromeOptions()
        # option.headless = True
        self.driver = Chrome(options=option)
        self.driver.maximize_window()
        search_query = self.search_query.replace(' ', '+')
        n_base_url = 'https://www.amazon.com/s?k={0}'.format(search_query)
        self.driver.get(n_base_url)
        time.sleep(1)
        department_list = []
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        departments_main = soup.find('div',id='departments')
        for each in departments_main.find_all('span',class_="a-list-item"):
            try:
                value = str(each.text).strip()
                href = str(base_url + each.a['href']).strip()

                # print(value,href)
                if '\n' in value:
                    pass
                else:
                    self.keywords.add(value)
                    department_list.append([value, href,0])
                    print(value, href,0)
            except:
                continue

        # print('\ndone\n')

        for time_period in range(2):
            print('now started')
            sub_dept_value = self.sub_department(department_list)
            if sub_dept_value == False:
                break
            else:
                # print(f'\nthis is the length of the sub-departments {len(sub_dept_value)}\n')
                # print(f'\nthis is the length of the sub-departments {len(self.keywords)}\n')

                # print('\ndone_2\n')
                print('\ntotal departments ',len(sub_dept_value))
                print('')
                # time.sleep(2)
                # break
                # time.sleep(4)
                # print(len(department_list))
                # self.driver.quit()
                # time.sleep(10)
                # counter = 0
                # for i in sub_dept_value:
                #     print(counter)
                #     print(i)
                # #     department_list.append(i)
                #     counter+=1
                # print('\ndone_3\n')

                # for i in department_list:
                    # print(i)
        for i in department_list:
            print(i)
        # headers = ["Department Keyword", "Link","0","1"]
        # df = pandas.DataFrame(department_list, columns=headers)
        # ex_filename = (f"{q}_department_kwywords.xlsx")
        # df[["Department Keyword", "Link"]].to_excel(ex_filename)

        # for i in department_list:
        #     print(i)

        for department in department_list:
            self.for_multiprocessing(department_name=department[0],department_link=department[1])

    def check_checked(self,lst):
        for i in lst:
            if i[-1] == 0:
                return 'unchecked'
        return 'checked'

    def sub_department(self,dept_list):

        if self.check_checked(dept_list) == 'unchecked':
            for link in range(len(dept_list)):
                # print(dept_list[link])
                if dept_list[link][-1] == 0:
                    # start new department
                    self.driver.get(dept_list[link][1])
                    dept_list[link].append(1)
                    time.sleep(1)
                    soup = BeautifulSoup(self.driver.page_source, 'lxml')
                    departments_main = soup.find('div', id='departments')
                    print('\n',dept_list[link][0],dept_list[link][1])
                    try:
                        for each_sub in departments_main.find_all('li', class_="a-spacing-micro s-navigation-indent-2"):
                            if each_sub.span.a.span.text != '':
                                try:
                                    value = str(each_sub.text).strip()
                                    href = str(base_url + each_sub.span.a['href']).strip()
                                    # print(value)
                                    if value not in self.keywords:
                                        self.keywords.add(value)
                                        dept_list.append([value, href,0])
                                        print('\t',value,href,0)
                                except:
                                    continue
                    except:
                        continue
            # print(self.keywords)
            return dept_list

        elif self.check_checked(dept_list) == 'checked':
            return False

    def for_multiprocessing(self,department_name,department_link):

        self.driver.get(department_link)
        try:
            el = self.driver.find_element(By.ID,'s-result-sort-select')
            for option in el.find_elements(By.TAG_NAME,'option'):
                if 'customer review' in option.text.lower():
                    # print("found")
                    option.click()
                    break
        except:
            pass

        temp_soup = BeautifulSoup(self.driver.page_source, 'lxml')

        filter_links = temp_soup.find('div', id='priceRefinements')

        price_range_lst = []

        try:
            for each in filter_links.find_all('li', class_='a-spacing-micro'):
                try:
                    value = str(each.text).strip()
                    href = str(base_url + each.span.a['href']).strip()
                    price_range_lst.append([value, href])
                except:
                    continue
        except:
            self.invalid_links_data.append([department_name,department_link])

        # print('hehehehe')
        # time.sleep(10)
        print(len(self.invalid_links_data))
        for i in price_range_lst:
            self.search_each_page(department_name, position=i[0], n_link=i[1])


    def search_each_page(self,department,position,n_link):
        self.data.append([f'{department}', None, None, None, None, None])
        self.data.append([f'{position}', None, None, None, None, None])

        self.driver.get(n_link)
        print(n_link)

        for i in range(1,51):

            current_scroll_position, new_height = 0, 1
            while current_scroll_position <= new_height:
                current_scroll_position += 40
                self.driver.execute_script("window.scrollTo(0, {});".format(current_scroll_position))
                new_height = self.driver.execute_script("return document.body.scrollHeight")

            try:
                next_page = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"a.s-pagination-next")))
            except:
                break

            time.sleep(2)

            print(f'Processing keyword {search_query} for department {department} for price {position} at page {i}')

            page_html = self.driver.page_source
            soup = bs4.BeautifulSoup(page_html, 'lxml')

            products_on_page = soup.find_all("div", attrs={"class": ["s-result-item"]})

            time.sleep(2)

            self.scrape_product_information(products_on_page)

            time.sleep(2)

            classes = next_page.get_attribute("class")


            if "s-pagination-disabled" in classes:
                break

            next_page.click()

        self.write_to_excel()

    def scrape_product_information(self,products):

        for each in products[1:]:
            try:
                product_a = each.find_all("a",attrs={"class":["s-underline-link-text","a-text-normal"]})

                p_a = 0
                if product_a==[]:
                    continue
                for x in product_a:
                    if 'feedback' in x.text:
                        continue
                    p_a = x
                    break
                product_href = p_a["href"]
                product_href = self.base_url+product_href
                try:
                    product_name = p_a.find_all("span")[0].text
                except:
                    continue
                try:
                    product_p = each.find_all("span",attrs={"class":["a-price"]})[0]
                    product_price = '$'+str(product_p.text).split('$')[1]
                except:
                    product_price = 0

                try:
                    rating = each.find('i', {'class': 'a-icon'}).text
                    try:
                        rating_count = each.find_all('span', {'aria-label': True})[1].text
                    except:
                        rating_count = 0
                except AttributeError:
                    # print(product_name)
                    continue

                product_i = each.find_all("img",attrs={"class":["s-image"]})[0]
                product_image = product_i["src"]

                self.data.append([product_href,product_name,product_price,product_image, rating,rating_count])
            except:
                continue

    def write_to_excel(self):
        writer = pandas.ExcelWriter(self.excel_name, engine='xlsxwriter')
        headers = ["LINK","NAME","PRICE","IMAGE","RATING","RATING COUNT"]
        df = pandas.DataFrame(self.data,columns=headers)
        df.to_excel(writer, sheet_name='Valid Data')

        headers_2 = ["DEPARTMENT NAME","LINK"]
        df_2 = pandas.DataFrame(self.invalid_links_data, columns=headers_2)
        df_2.to_excel(writer,sheet_name='Invalid Department Links Data')

        writer.save()


if __name__ == '__main__':

    base_url = 'https://www.amazon.com/'
    search_query = 'shoe'
    price_range = [
                   ['50', '100'],
                   ['100', '200']
    ]

    AmazonScraper(base_url,search_query,price_range)
