import os
import mechanicalsoup
import argparse
import math

parser = argparse.ArgumentParser(description='Download Giantbomb Videos')
parser.add_argument('username')
parser.add_argument('password')
parser.add_argument('query')
args = parser.parse_args()

browser = mechanicalsoup.Browser()

#Login
print("Logging in...")
login_page = browser.get('http://auth.giantbomb.com/login')
login_form = login_page.soup.select('#login')[0]
login_form.select('input')[0]['value'] = args.username
login_form.select('input')[1]['value'] = args.password
page2 = browser.submit(login_form, login_page.url)

#Verify login worked
check = browser.get("http://auth.giantbomb.com/account")
logged_in = False
for tag in check.soup.p:
    if args.username in tag.string:
        logged_in = True



if logged_in:
    try:
        ignore_links = open('ignore').readlines()
    except:
        ignore_links = []
    query = args.query.replace(' ', '%20')
    query_url = "http://www.giantbomb.com/search/?indices[0]=video&page=1&q=" + query
    print("Searching for '" + args.query + "'...")

    search_page = browser.get("http://www.giantbomb.com/search/?indices[0]=video&page=1&q="+ query_url)
    try:
        results_str = search_page.soup.find('li', class_='paginate__results').string
        num_results = int(results_str[0:results_str.find(' ')])
        print(str(num_results) + " results")
    except:
        num_results = 15
        print("Less than 15 results")
    num_pages = math.ceil(num_results/15)

    page_links = []
    print("Writing links to file...")
    for i in list(range(1, num_pages+1)):
        page = browser.get('http://www.giantbomb.com/search/?indices[0]=video&page=' + str(i) + '&q=' + query)
        results = page.soup.find_all('a', class_="js-ajax-api-track-anchor")
        for x in list(range(len(results))):
           page_links.append(results[x]['href'])
    try:
        os.remove('search_results')
    except:
        None
    with open("search_results", "a") as text:
        for x in page_links:
            text.write('http://www.giantbomb.com' + x + '\n')
    input("Press enter to choose which videos to download") 
    os.system('vim search_results')
    print("Retrieving video links...")
    final_list = open("search_results").readlines()
    video_urls = []
    for i in list(range(len(final_list))):
        final_list[i] = final_list[i][:len(final_list[i])-1]
        video_page = browser.get(final_list[i])
        url = video_page.soup.find_all('ul', class_='pull-bottom')[0].find_all('a', text='High')[0].attrs['href']
        duplicate = False
        for i in ignore_links:
            if url in i:
                duplicate = True
        if not duplicate:
            video_urls.append(url)
    if not os.path.isdir("~/'Giant Bomb'/" + args.query):
        os.system("mkdir -p ~/'Giant Bomb'/'" + args.query + "'")
    for i in list(range(len(video_urls))):
        print("Downloading video " + str(i+1) +"/" + str(len(video_urls)))
        command = "cd ~/'Giant Bomb'/'" + args.query + "'  && { curl -O " + video_urls[i] +" ; cd -; }"
        print(command)
        os.system(command)
        ignore_links.append(video_urls[i])
    with open('ignore', 'w') as text:
        for x in ignore_links:
            text.write(x + '\n')
    os.system('rm search_results')
else:
    print("Error logging in, please try again")
