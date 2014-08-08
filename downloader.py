import os
import mechanicalsoup
import argparse
import math

def find_s(s, ch):
    return [i for i, ltr in enumerate(s) if ltr ==ch]

def get_filename(url):
    return url[find_s(url, "/")[len(find_s(url, "/"))-1]+1:]

parser = argparse.ArgumentParser(description='Download Giantbomb Videos')
parser.add_argument('query')
parser.add_argument("-q", "--quality", type=str)
args = parser.parse_args()

browser = mechanicalsoup.Browser()

username = input("Please enter your Giant Bomb premium username: ")
password = input("Please enter your password: ")

#Default to High
if args.quality == None:
    quality = "High"
else:
    quality = args.quality

#Login
print("Logging in...")
login_page = browser.get('http://auth.giantbomb.com/login')
login_form = login_page.soup.select('#login')[0]
login_form.select('input')[0]['value'] = username
login_form.select('input')[1]['value'] = password
page2 = browser.submit(login_form, login_page.url)

#Verify login worked
check = browser.get("http://auth.giantbomb.com/account")
logged_in = False
for tag in check.soup.p:
    if username in tag.string:
        logged_in = True

if logged_in:
    #Get list of already downloaded videos
    try:
        ignore_links = open('ignore').readlines()
    except:
        ignore_links = []
    #Clean up query format and create link
    query = args.query.replace(' ', '%20')
    query_url = "http://www.giantbomb.com/search/?indices[0]=video&page=1&q=" + query
    print("Searching for '" + args.query + "'...")

    search_page = browser.get("http://www.giantbomb.com/search/?indices[0]=video&page=1&q="+ query_url)
    #Search page only shows number of results if there's more than one page for some reason - make it 15 because 15/15 = 1 page
    try:
        results_str = search_page.soup.find('li', class_='paginate__results').string
        num_results = int(results_str[0:results_str.find(' ')])
        print(str(num_results) + " results")
    except:
        num_results = 15
        print("Less than 15 results")
    num_pages = math.ceil(num_results/15)
    #Iterate through search result pages and generate list of links to the video pages - still not video file itself.
    page_links = []
    print("Writing links to file...")
    for i in list(range(1, num_pages+1)):
        page = browser.get('http://www.giantbomb.com/search/?indices[0]=video&page=' + str(i) + '&q=' + query)
        results = page.soup.find_all('a', class_="js-ajax-api-track-anchor")
        for x in list(range(len(results))):
           page_links.append(results[x]['href'])
    #Write links to file to allow user to curate
    with open("search_results", "w") as text:
        for x in page_links:
            text.write('http://www.giantbomb.com' + x + '\n')
    input("Press enter to choose which videos to download") 
    os.system('vim search_results')
    print("Retrieving video links...")
    final_list = open("search_results").readlines()
    #Iterate through video pages and grab the video links - discarding if already downloaded
    video_urls = []
    names = []
    for i in list(range(len(final_list))):
        final_list[i] = final_list[i][:len(final_list[i])-1]
        video_page = browser.get(final_list[i])
        url = video_page.soup.find_all('ul', class_='pull-bottom')[0].find_all('a', text=quality)[0].attrs['href']
        name = video_page.soup.h2.string
        duplicate = False
        for i in ignore_links:
            if url in i:
                duplicate = True
        if not duplicate:
            video_urls.append(url)
            names.append(name)
    #Make a folder named for the query if not already existing
    if not os.path.isdir("~/'Giant Bomb'/" + args.query):
        os.system("mkdir -p ~/'Giant Bomb'/'" + args.query + "'")
    #Download videos
    for i in list(range(len(video_urls))):
        print("Downloading video " + str(i+1) +"/" + str(len(video_urls)))
        command = "cd ~/'Giant Bomb'/'" + args.query + "'  && { curl -O " + video_urls[i] +" ; mv " + get_filename(video_urls[i]) + " '" + names[i] + video_urls[i][-4:] + "'; cd -; }"
        print(command)
        os.system(command)
        ignore_links.append(video_urls[i])
    #Add videos to ignore list
    with open('ignore', 'w') as text:
        for x in ignore_links:
            if x == ignore_links[len(ignore_links)-1]:
                text.write(x)
            else:
                text.write(x + '\n')
    #Clean up
    os.system('rm search_results')
else:
    print("Error logging in, please try again")
