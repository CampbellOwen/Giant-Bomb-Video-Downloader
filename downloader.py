import os
import mechanicalsoup
import argparse
import math
import getpass

def find_s(s, ch):
    return [i for i, ltr in enumerate(s) if ltr ==ch]

def get_filename(url):
    return url[find_s(url, "/")[len(find_s(url, "/"))-1]+1:]
def fix_names(names):
    name_list = []
    for name in names:
        print("Fixing name: "+name)
        slash_index = name.find('/')
        if slash_index == -1:
            break
        month = name[slash_index-2:slash_index]
        day = name[slash_index+1:slash_index+3]
        year = name[slash_index+4:slash_index+8]
        print("Month: " + month)
        print("Day: " + day)
        print("Year: " + year)
        name = name[:slash_index-2] + year + '.' + month + '.' + day + name[slash_index+8:]
        name = name.replace('/', '.')
        name = name.replace("'", "")
        print("Final name: "+name)
        name_list.append(name)
    return name_list



browser = mechanicalsoup.Browser()

search = 1
content = str(input("Please enter type of download (video or podcast): "))
if content == 'video':
    quality = str(input("Please enter quality of video (Mobile, Low, Med, High, or HD: "))
if content == 'podcast':
    print("Would you like to search for a specific podcast or browse a category?\n1. Search\n2. Browse")
    if int(input()) == 2:
        search = 0
        print("Enter podcast category:\n1. Giant Bombcast\n2. Premium Podcasts\n3. 8-4 Play\n4. Giant Bomb Gaming Minute\n5. Giant Bomb's Interview Dumptruck\n6. Bombin' the A.M. With Scoops and the Wolf!\n7. Giant Bombcast (Premium)")
        choice = int(input())
        if choice == 1:
            query = ""
            folder = "Giant Bombcast"
        elif choice == 2:
            query = "premium/"
            folder = "Premium Podcasts"
        elif choice == 3:
            query = "eight-four-play/"
            folder = "Eight-Four Play"
        elif choice == 4:
            query = "giant-bomb-gaming-minute/"
            folder = "Giant Bomb Gaming Minute"
        elif choice == 5:
            query = "interview-dumptruck/"
            folder = "Interview Dumptruck"
        elif choice == 6:
            query = "bombin-the-a-m-with-scoops-and-the-wolf/"
            folder = "Bombin' the A.M. with Scoops and the Wolf"
        elif choice == 7:
            query = "premiumbombcast/"
            folder = "Premium Bombcast"

if search == 1:
    query = str(input("Enter your search query: "))
    folder = query


username = input("Please enter your Giant Bomb premium username: ")
password = getpass.getpass("Please enter your password: ")

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
    #Get ignore list
    try:
        ignore_links = open('ignore').readlines()
        #Remove \n
        for i in list(range(len(ignore_links))):
            ignore_links[i] = ignore_links[i][:-1]
    except:
        ignore_links = []
    if search == 1:
        #Clean up query format and create link
        query = query.replace(' ', '%20')
        query_url = "http://www.giantbomb.com/search/?indices[0]="+content+"&page=1&q=" + query
        print("Searching for '" + query + "'...")

        search_page = browser.get("http://www.giantbomb.com/search/?indices[0]="+content+"&page=1&q="+ query_url)
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
            page = browser.get('http://www.giantbomb.com/search/?indices[]='+content+'&page=' + str(i) + '&q=' + query)
            results = page.soup.find_all('a', class_="js-ajax-api-track-anchor")
            for x in list(range(len(results))):
               page_links.append(results[x]['href'])

        #Write links to file to allow user to curate
        with open("search_results", "w") as text:
            for x in page_links:
                text.write('http://www.giantbomb.com' + x + '\n')
        input("Press enter to choose which "+content+"s to download") 
        os.system('vim search_results')

        print("Retrieving links...")
        final_list = open("search_results").readlines()
        #Iterate through video pages and grab the video links - discarding if already downloaded
        video_urls = []
        names = []
        if content == 'video':
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
        elif content == 'podcast':
            for i in list(range(len(final_list))):
                final_list[i] = final_list[i][:len(final_list[i])-1]
                print(final_list[i])
                video_page = browser.get(final_list[i])
                url = video_page.soup.find_all('a', id='top_podcast')[0].attrs['href']
                url = "http://v.giantbomb.com/podcast/"+url[47:]
                name = video_page.soup.h2.string
                duplicate = False
                for i in ignore_links:
                    if url in i:
                        duplicate = True
                if not duplicate:
                    video_urls.append(url)
                    names.append(name)
    elif search == 0:
        url = "http://www.giantbomb.com/podcasts/"+query
        print(url)
        podcast_page = browser.get(url)
        num_results_string = podcast_page.soup.find('li', class_='paginate__results').string
        num_results = num_results_string[:num_results_string.find(" ")]
        print(num_results)
        podcast_sidebar = podcast_page.soup.find('div', class_='aside-pod')
        podcast_link_list = []
        navigation_bar = podcast_page.soup.find('div', class_='navigation')
        num_pages = navigation_bar.find('ul').find_all('li')[7].find('a').string
        print(num_pages)
        for j in list(range(1,int(num_pages)+1)):
            print(url+"?page="+str(j))
            page = browser.get(url+"?page="+str(j))
            sidebar = page.soup.find('div', class_='aside-pod')
            podcast_list = sidebar.find('ul').find_all('li')
            for i in list(range(len(podcast_list))):
                podcast_link_list.append(podcast_list[i].find('a').attrs['href'])
        print(podcast_link_list)
        print(str(len(podcast_link_list)))
        #Write links to file to allow user to curate
        with open("search_results", "w") as text:
            for x in podcast_link_list:
                text.write('http://www.giantbomb.com' + x + '\n')
        input("Press enter to choose which "+content+"s to download") 
        os.system('vim search_results')
        print("Retrieving links...")
        final_list = open("search_results").readlines()
        video_urls = []
        names = []
        for i in list(range(len(final_list))):
            final_list[i] = final_list[i][:len(final_list[i])-1]
            print(final_list[i])
            video_page = browser.get(final_list[i])
            url = video_page.soup.find_all('a', id='top_podcast')[0].attrs['href']
            url = "http://v.giantbomb.com/podcast/"+url[47:]
            name = video_page.soup.h2.string
            duplicate = False
            for i in ignore_links:
                if url in i:
                    duplicate = True
            if not duplicate:
                video_urls.append(url)
                names.append(name)

    names = fix_names(names)
    #Make a folder named for the query if not already existing
    if not os.path.isdir("~/'Giant Bomb'/" + folder):
        os.system("mkdir -p ~/'Giant Bomb'/'" + folder + "'")
    #Download videos
    for i in list(range(len(video_urls))):
        print("Downloading "+ content  + str(i+1) +"/" + str(len(video_urls)))
        command = "cd ~/'Giant Bomb'/'" + folder + "'  && { curl -O " + video_urls[i] +" ; mv " + get_filename(video_urls[i]) + " '" + names[i] + video_urls[i][-4:] + "'; cd -; }"
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
