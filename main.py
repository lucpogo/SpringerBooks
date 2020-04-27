# %%
import os
import requests
import bs4
import urllib
import sys
from math import ceil
from tqdm import tqdm
from unicodedata import normalize

# %%
books_per_page = 10
url_categories = 'https://link.springer.com/search/facetexpanded/discipline?facet-content-type=%22Book%22&package=mat-covid19_textbooks'
urlbase = 'https://link.springer.com/'
if len(sys.argv)==1:
    destination=os.path.dirname(os.path.realpath(__file__))
else:
    destination=sys.argv[1]
# %%
def getCategories(url_categories):
    res = requests.get(url_categories)
    content = bs4.BeautifulSoup(res.text,'html.parser')
    number_of_classes = int(content.select_one('.number-of-pages').text)
    categories = []
    for c in range(1,number_of_classes+1):
        res = requests.get(url_categories+f'&page={c}')
        content = bs4.BeautifulSoup(res.text,'html.parser')
        category_buffer = [x.select_one('a').text.split('\n')[2] for x in content.select_one('ol').select('li')]
        categories.extend(category_buffer)
    return categories

def downloadCategory(category,urlbase,destination):
    query = 'facet-content-type=' + urllib.parse.quote_plus('\"Book\"') + '&just-selected-from-overlay-value=' + urllib.parse.quote_plus(f'\"{category}\"') + '&just-selected-from-overlay=facet-discipline&package=mat-covid19_textbooks&facet-discipline='+ urllib.parse.quote_plus(f'\"{category}\"')
    url_category = f'https://link.springer.com/search?{query}'
    res = requests.get(url_category)
    content = bs4.BeautifulSoup(res.text,'html.parser')
    number_of_books = int(content.select_one('#number-of-search-results-and-search-terms').select_one('strong').text)
    if number_of_books>0:
        print(f'Downloading {number_of_books} book for {category}')
        number_of_pages = ceil(number_of_books/books_per_page)#int(content.select_one('.number-of-pages').text)
        book_list=[]
        with tqdm(total=number_of_books) as pbar:
            for n in range(1,number_of_pages+1):
                url_category = f'https://link.springer.com/search/page/{n}?{query}'
                res = requests.get(url_category)
                content = bs4.BeautifulSoup(res.text,'html.parser')
                book_list = [x.select_one('a').get_attribute_list('href')[0] for x in content.select_one('.content-item-list').select('h2')]
                for book_url in book_list:
                    downloadBook(urlbase+book_url,category,urlbase,destination)
                    pbar.update(1)

def downloadBook(book_url,category,urlbase,destination):
    res = requests.get(book_url)
    content = bs4.BeautifulSoup(res.text,'html.parser')
    title = content.select_one('.page-title').select_one('h1').text
    authors = '; '.join([normalize('NFKC',x.text) for x in content.select('.authors__name')])
    download_link = content.select_one('a[data-track-action=\"Book download - pdf\"]').get_attribute_list('href')[0]
    if not os.path.exists(os.path.join(destination,category.replace('/','-'))):
        os.mkdir(os.path.join(destination,category.replace('/','-')))
    r = requests.get(urlbase + download_link)
    with open(os.path.join(destination,category.replace('/','-'),'(' + authors.replace('/','_') +') ' + title.replace('/','_') +'.pdf'),'wb') as f:
        f.write(r.content)

# %%
if os.path.exists(destination):
    print(f'Downloading books into {destination}')
    categories = getCategories(url_categories)

    for category in categories:
        downloadCategory(category,urlbase,destination)
    print('Done!!!')
else:
    print(f'Path {destination} doesn\'t exist')
