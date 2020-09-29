#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 10 12:10:55 2020

@author: zeynepisik
"""

import urllib.request, json
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from ahocorapy.keywordtree import KeywordTree
import time
import xlsxwriter


page_limit = 100
rule_sets_file = "rule_sets.json"

## method to send request by paging
def request(page):
    with urllib.request.urlopen("http://mock.artiwise.com/api/news?_page="+ str(page)+"&_limit=1000") as url:
        return json.loads(url.read().decode())

## method to read rule sets
def read_rule_sets(file):
    with open(file) as json_file:
        return json.load(json_file)
    
## normalize title + description + content
## pass the news that having no description 
def normalize_text(data):
    
    text = ""
    if data['lang'] == "tr":
        tr_sw = set(stopwords.words('turkish'))
    
        try:
            text = data["title"] + " " + data["description"] + " " + data["content"]
            text = re.sub(' +', ' ', re.sub(r'[^\w\s]','',text.lower())) ## lowercase, remove punctuation, remove extra whitespace
            w_list = word_tokenize(text)
            tokens_without_sw = [word for word in w_list if not word in tr_sw] #remove stopwords
            text = " ".join(tokens_without_sw)
            
        except:
            pass
        
        
    elif data['lang'] == "en":
        en_sw = set(stopwords.words('english'))
        
        try:
            text = data["title"] + " " + data["description"] + " " + data["content"]
            text = re.sub(' +', ' ', re.sub(r'[^\w\s]','',text.lower())) ## lowercase, remove punctuation, remove extra whitespace
            w_list = word_tokenize(text) 
            tokens_without_sw = [word for word in w_list if not word in en_sw]  #remove stopwords
            text = " ".join(tokens_without_sw)
        except:
            pass
    
    else:
        fr_sw = set(stopwords.words('french'))
        
        try:
            text = data["title"] + " " + data["description"] + " " + data["content"]
            text = re.sub(' +', ' ', re.sub(r'[^\w\s]','',text.lower())) ## lowercase, remove punctuation, remove extra whitespace
            w_list = word_tokenize(text) 
            tokens_without_sw = [word for word in w_list if not word in fr_sw] #remove stopwords
            text = " ".join(tokens_without_sw)
        except:
            pass
        
    
    return text
    
## run all_match 
def ahocorasick_all_match(text, keywords):
    kwtree_all = KeywordTree(case_insensitive=True)
    for key in keywords:
        kwtree_all.add(key)
    kwtree_all.finalize()
    
    all_match = list()
    results = kwtree_all.search_all(text)
    for result in results:
        if result[0] in all_match:
            pass
        else:
            all_match.append(result[0])
        
    return len(all_match)

## run any_match
## text_info (rule_set["set_id"],[text, rules["rule_name"], rules["name"], rules["lang"], rules["type"], rules["tags"], rules["categories"], news_data[i], rule_set["set_name"]])
def ahocorasick_any_match(text_info):
    kwtree_any = KeywordTree(case_insensitive=True)
    bool_name = False
    bool_lang = False
    bool_type = False
    bool_tags = False
    bool_categories = False
    
    """
    CREATE TREE
    
    """
    ## if name condition is empty, (name is a string)
    if not text_info[1][2]:
        bool_name = True
        
    else:
        kwtree_any.add(text_info[1][2]) ## add name condition into aho corasick tree
         
    ## if lang condition is empty, (lang is a string)
    if not text_info[1][3]:
        bool_lang = True
        
    else:
        kwtree_any.add(text_info[1][3]) ## add lang condition into aho corasick tree
        
    ## if type condition is empty, (type is a string)
    if not text_info[1][4]:
        bool_type = True
        
    else:
        kwtree_any.add(text_info[1][4]) ## add type condition into aho corasick tree
        
    
    ## if tags condition is empty, (tags is a list)
    if not text_info[1][5]:
        bool_name = True
        
    else:
        for tag in text_info[1][5]:
            kwtree_any.add(tag) ## add tag conditions into aho corasick tree 
        
    
    ## if categories condition is empty, (categories is a list)
    if not text_info[1][6]:
        bool_name = True
        
    else:
        for categ in text_info[1][6]:
            kwtree_any.add(categ) ## add categories conditions into aho corasick tree 
    
    
    kwtree_any.finalize()

    """
    ANY MATCH
    
    """  
    ## name
    if kwtree_any.search_one(text_info[1][7]["name"]):
        bool_name = True
    
    ## lang
    if kwtree_any.search_one(text_info[1][7]["lang"]):
        bool_lang = True
    
    ## type
    if kwtree_any.search_one(text_info[1][7]["type"]):
        bool_type = True
        
    ## tags
    tags = helper_list_to_str(text_info[1][7]["tags"])
    if kwtree_any.search_one(tags):
        bool_tags = True
        
    ## categories
    categs = helper_list_to_str(text_info[1][7]["categories"])
    if kwtree_any.search_one(categs):
        bool_categories = True
        
    
    """
    RESULT
    """
    
    if bool_name and bool_lang and bool_type and bool_tags and bool_categories:
        
        return text_info
    else:
        return False
    
    
def helper_list_to_str(l):
    res = ""
    for e in l:
        res = res + e + " "
    return res

def print_excel(results):
    
    workbook = xlsxwriter.Workbook('results.xlsx')
    worksheet = workbook.add_worksheet()
        
    worksheet.write('A' + str(1), "rule set" )
    worksheet.write('B'+ str(1), "id")
    worksheet.write('C'+ str(1), "url")
    worksheet.write('D'+ str(1), "name")
    worksheet.write('E'+ str(1), "lang")
    worksheet.write('F'+ str(1), "type")
    worksheet.write('G'+ str(1), "tags")
    worksheet.write('H'+ str(1), "categories")
    worksheet.write('I'+ str(1), "title")
    worksheet.write('J'+ str(1), "description")
    worksheet.write('K'+ str(1), "content")
    worksheet.write('L'+ str(1), "crawl_date")
    worksheet.write('M'+ str(1), "modified_date")
    worksheet.write('N'+ str(1), "published_date")
    worksheet.write('O'+ str(1), "text")
    worksheet.write('P'+ str(1), "rules")
        
    for a, res in enumerate(results):
        worksheet.write('A'+ str(a+2), res[1][8])
        worksheet.write('B'+ str(a+2), res[1][7]["id"])
        worksheet.write('C'+ str(a+2), res[1][7]["url"])
        worksheet.write('D'+ str(a+2), res[1][7]["name"])
        worksheet.write('E'+ str(a+2), res[1][7]["lang"])
        worksheet.write('F'+ str(a+2), res[1][7]["type"])
        worksheet.write_row('G'+ str(a+2), res[1][7]["tags"])
        worksheet.write_row('H'+ str(a+2), res[1][7]["categories"])
        worksheet.write('I'+ str(a+2), res[1][7]["title"])
        worksheet.write('J'+ str(a+2), res[1][7]["description"])
        worksheet.write('K'+ str(a+2), res[1][7]["content"])
        worksheet.write('L'+ str(a+2), res[1][7]["crawl_date"])
        worksheet.write('M'+ str(a+2), res[1][7]["modified_date"])
        worksheet.write('N'+ str(a+2), res[1][7]["published_date"])
        worksheet.write('O'+ str(a+2), res[1][0])
        worksheet.write('P'+ str(a+2), res[1][1])
        
    
    workbook.close()
    

                
     
"""
Rule set record format:
   
[
	{
		"set_name": int,
		"rules": [
			{   "rule_id": int
				"rule_name": "",
				"keywords": [],
				"name": "",
				"lang": "",
				"type": "",
				"tags": [],
				"categories": [],
				"title": "",
				"description": "",
				"content": ""
			}
		]
	}
]
"""

start_time = time.time()

rule_sets = read_rule_sets(rule_sets_file)
page = 1 ## because page 0 and page 1 are same
full_page = True
text_list = []
filtered_news = []
response = 0
while full_page:
    news_data = request(page)
    if not news_data:
        full_page = False
    else:
        page += 1
        
        ## read rule sets and run aho corasick
        for i in range(page_limit):
            text = normalize_text(news_data[i])
            for rule_set in rule_sets:
                ## run aho corasick for keywords => all match condition
                for rules in rule_set["rules"]:
                    all_match = ahocorasick_all_match(text, rules["keywords"]) ## keywordler tek seferde çarpıyor
                    if len(rules["keywords"]) != all_match:
                        response += 1
                        continue
                    
                    else:
                        response += 1
                        text_list.append((rule_set["set_id"],[text, rules["rule_name"], rules["name"], rules["lang"], rules["type"], rules["tags"], rules["categories"], news_data[i], rule_set["set_name"]]))
                    
        ## run aho corasick for other conditions => any match condition    
        
        if response % 100 == 0:
            #print("nbr")
            for t in text_list:
                if ahocorasick_any_match(t) is False:
                    pass
                else:
                    filtered_news.append(ahocorasick_any_match(t))
        text_list = []
    break 
        
## sort the results according to set id and print the results on excel file
filtered_news = sorted(filtered_news, key=lambda x: x[0], reverse=False)
print_excel(filtered_news)
                    
print("--- %s seconds ---" % (time.time() - start_time))