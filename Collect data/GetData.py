from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import markdownify
import json
import html5lib
from time import sleep
import concurrent.futures

def GetCleanedContent(text):
    # Удаление HTML-тегов и ненужных пробелов
    x = 0
    while(x < len(text)):
        if(text[x] == '<'):
            index = text.find('>', x)
            if(text[x+1:index] == 'code'):
                x = text.find('</code>', x) + 7
            else:
                text = text.replace(text[x:index+1], "", 1)
        else:
            x += 1
    return text.replace('&nbsp;', ' ').strip(' ')

def GetDescription(driver):
    try:
        description = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.flexlayout__tab [data-track-load="description_content"]'))
        )
        # data[name]["problem"] = ""
        for p in description.find_elements(By.TAG_NAME, "p"):
            if 'example' in p.text.lower():
                break
            text = GetCleanedContent(p.get_attribute('innerHTML'))
            text = markdownify.markdownify(text, heading_style='SETEXT')
            # data[name]["problem"] += text + '\n'
            return text + '\n'
    except Exception as e:
        print(f"Error in GetDescription: {e}")

def GetSolutionFromEdutorial(driver):
    try:
        solution = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "FN9Jv"))
        )
        a = solution.get_attribute('innerHTML')
        approaches = solution.find_elements(By.TAG_NAME, "h3")
        a = a[a.find(approaches[-1].text):]
        explanation = markdownify.markdownify(a[a.find('Algorithm'):a.find('Implementation')], heading_style='SETEXT')
        # data[name]["explanation"] = m
        
        # Получаем URL для реализации
        implementation_url = ''
        for iframe in solution.find_elements(By.TAG_NAME, "iframe"):
            src = iframe.get_attribute('src')
            if 'https://leetcode.com/playground/' in src:
                implementation_url = src
                break
        
        if implementation_url:
            driver.get(implementation_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror-lines"))
            )
            buttons = driver.find_element(By.CLASS_NAME, "lang-btn-set").find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if 'py' in button.text.lower():
                    button.click()
                    break

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "CodeMirror-code"))
            )
            lines = driver.find_element(By.CLASS_NAME, "CodeMirror-lines").find_element(By.CLASS_NAME, "CodeMirror-code").find_elements(By.TAG_NAME, "pre")
            code = '```python\n' + '\n'.join(line.text for line in lines) + '\n```'
            # data[name]["solution"] = code
        return [True, explanation, code]
    except Exception as e:
        # print(f"Error in GetSolutionFromEdutorial: {e}")
        return [False, '', '']

def GetCodeFromPeople(driver):
    try:
        languages = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@class="flex select-none bg-layer-2 dark:bg-dark-layer-2"]/div'))
        )
        for language in languages:
            if 'py' in language.text.lower():
                language.click()
                break
    finally:
        try:
            codeBlocks = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'code'))
            )
            
            text = '```python\n'
            for code in codeBlocks:
                code = code.get_attribute('innerHTML')
                if('Solution' in code):
                    soup = BeautifulSoup(code, 'html5lib')
                    for code_span in soup.find_all('span'):
                        ok = True
                        for span in code_span.find_all('span'):
                            if(len(span.get_text(separator='\n', strip=False)) == 0):
                                text += '\n'
                            else:
                                text += span.get_text(separator='\n', strip=False)
                            ok = False
                        if(ok):
                            text += code_span.get_text(separator='\n', strip=False)
                    break
            text += '\n```'
            return text
        except Exception as e:
            print(repr(e))
            return ''

def GetExplanationFromPeople(driver, times=0):
    try:
        arrow_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@class="mt-[3px] cursor-pointer text-[0px] transition-transform text-lc-icon-secondary dark:text-dark-lc-icon-secondary hover:text-lc-icon-primary dark:hover:text-dark-lc-icon-primary"]'))
        )
        arrow_button.click()

        languages_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//*[@class="inline-flex cursor-pointer items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-[3px] text-xs bg-lc-fill-02 dark:bg-dark-lc-fill-02 text-lc-text-secondary dark:text-dark-lc-text-secondary"]'))
        )
        for language in languages_buttons:
            if 'py' in language.text.lower():
                language.click()
                break
        arrow_button.click()
        global isFirstTime
        if isFirstTime:
            isFirstTime = False
            sort_arrow = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@class="flex items-center text-left cursor-pointer focus:outline-none whitespace-nowrap rounded-[4px] px-1 py-0.5 text-sm text-text-tertiary dark:text-text-tertiary hover:text-text-secondary dark:hover:text-text-secondary bg-transparent dark:bg-dark-transparent active:bg-transparent dark:active:bg-dark-transparent hover:bg-transparent dark:hover:bg-transparent"]'))
            )
            sort_arrow.click()
            sort_buttons = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@role="menuitem"]'))
            )
            for button in sort_buttons:
                if 'votes' in button.text.lower():
                    button.click()
                    break
        sleep(2)

        link_to_solution = WebDriverWait(WebDriverWait(WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, './/*[@class="group flex w-full cursor-pointer flex-col gap-1.5 px-4 pt-3"]'))
        )[times], 10).until(
            EC.presence_of_element_located((By.XPATH, './/*[@class="overflow-hidden text-ellipsis"]'))
        ), 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'a'))
        ).get_attribute('href')

        driver.get(link_to_solution)
        solution = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@class="FN9Jv WRmCx"]'))
        )
        a = solution.get_attribute('innerHTML')
        start1 = a.find('>', a.find('id="approach')) + 1
        end1 = a.find('id="', start1)
        start2 = a.find('>', a.find('id="explanation')) + 1
        end2 = a.find('id="', start2)
        if len(a[start1:end1]) == 0 and len(a[start2:end2]) == 0:
            return [True, '', '']
        end = start = 0
        if(end1 - start1 >= end2 - start2):
            end = end1
            start = start1
        else:
            end = end2
            start = start2
        for i in range(end, end - 20, -1):
            if a[i] == '<':
                end = i
                break
        explanation = markdownify.markdownify(a[start:end], heading_style='SETEXT')
        # data[name]["explanation"] = m
        code = GetCodeFromPeople(driver)
        return [False, explanation, code]
    except Exception as e:
        # print(f"Error in GetExplanationFromPeople: {e}")
        return [True, '', '']

def GetSolutionFromPeople(driver):
    times = 0
    explanation = code = ''
    ok = True
    while(times < 5 and ok):
        ok, explanation, code = GetExplanationFromPeople(driver, times)
        driver.back()
        sleep(2)
        times += 1
    return [explanation, code]

def process_page(url):
    driver.get(url)
    problem_elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.odd\\:bg-layer-1'))
    )
    sleep(3)
    links = []
    for elem in problem_elements:
        name_element = elem.find_element(By.CSS_SELECTOR, '.h-5')
        link = name_element.get_attribute('href')
        if('?' in link):
            link = link[:link.find('?')]
        links.append((name_element.text, link))
    sleep(2)
    for name, link in links:
        # data[name] = {}
        driver.get(link)
        description = GetDescription(driver)
        new_link = link + ('editorial' if link[-1] == '/' else '/editorial')
        driver.get(new_link)
        try:
            ok, explanation, code = GetSolutionFromEdutorial(driver)
            if not ok:
                new_link = link + ('solutions' if link[-1] == '/' else '/solutions')
                driver.get(new_link)
                explanation, code = GetSolutionFromPeople(driver)
        except Exception as e:
            print(f"Error processing problem at {link}: {e}")
        if(description != '' and explanation != 'Approach\n' and code != '```python\n\n```'):
            data[name] = {}
            data[name]["problem"] = description
            data[name]["explanation"] = explanation
            data[name]["solution"] = code
        sleep(1)
        global i
        i += 1
        print(i)

# Constants
WaitTime = 3

# Selenium Setup
options = Options()
options.add_argument('--headless')  # Uncomment to run headlessx
driver = webdriver.Firefox(service=Service(), options=options)

# Global Variables
f = open('data.json', 'w')
data = dict()
isFirstTime = True
i = 0

# Processing pages in parallel
urls = [f'https://leetcode.com/problemset/?page={i}' for i in range(1, 67)]
# with ThreadPoolExecutor(max_workers=2) as executor:
#     executor.map(process_page, urls)
process_page(urls[0])
f.write(json.dumps(data, indent=4, ensure_ascii=False))
f.close()
