from bs4 import BeautifulSoup
import pycountry
import config
import requests
import discord
import time
import json
import re

client = discord.Client()

# Commands:
# respond to gwent link
# !player or !profile [gogname]
# !top10 open - open
# !top10 challenger - challenger
# !top10 masters - masters
# !rankings - open, challenger and masters rankings same as !top10masters
# !prorank - top mmr

# maybe:
# !tournaments - tournament schedule
# !decks [author]
# !news
# !latestnews
# add try/excepts, e.g. 'aggedon user profile'

# ideas:
# change embed color for faction

masters_logo_url = 'https://i.imgur.com/J37iggL.png'
playgwent_icon_url = 'https://i.imgur.com/ibtR9s0.png'
monsters_cardback = 'https://i.imgur.com/gGUkgTG.png'
nilfgaard_cardback = 'https://i.imgur.com/oUB0MQv.png'
skellige_cardback = 'https://i.imgur.com/8BwvANF.png'
northern_cardback = 'https://i.imgur.com/iVbOhbS.png'
scoiatel_cardback = 'https://i.imgur.com/Lx0cmbt.png'


def parse(link):
    r = requests.get(link, timeout=5)
    soup = BeautifulSoup(r.content, "html5lib")

    return soup

# fix to parse()
def parsequot(link):
    r = requests.get(link, timeout=5)
    soup = BeautifulSoup(r.content, "html5lib").findAll("div", {"data-state": True})

    string_link = str(soup)
    json_file = string_link.replace('&quot;', '"')
    json_file = json_file.split('data-state="', maxsplit=1)[-1]
    json_file = json_file.split('" data-translations', maxsplit=1)[0]

    json_file = json.loads(json_file)

    return json_file

def getCountry(code):
    return pycountry.countries.get(alpha_2=code).name

def getLink(string):
    link = re.search("(?P<url>https?://[^\s]+)", string).group("url")
    return link

def getProRank():
    soup = parse('https://masters.playgwent.com/en/rankings/pro-rank')
    prorank_description = soup.find('li', {'class': 'current'}).text.strip().lower().capitalize()
    soup = soup.find('div', {
        'class': 'c-ranking-table__body c-ranking-table__body--hover'}).findAll('div', {'class': 'c-ranking-table__tr'})

    prorank_url = 'https://masters.playgwent.com/en/rankings/pro-rank'

    data = [[] for n in range(5)]

    for n in range(5):
        country_code = str(soup[n].find('div').next_sibling.find('i')).split('icon-', 1)[-1].split('"', 1)[0].upper()
        country = getCountry(country_code)
        data[n].append(country)

        player = soup[n].find('div').next_sibling.find('strong').text
        data[n].append(player)

        matches = soup[n].find('span').text.split(' matches', 1)[0]
        data[n].append(matches)

        mmr = soup[n].find('div').next_sibling.next_sibling.find('strong').text.strip()
        data[n].append(mmr)

        nilfgaard_score = str(soup[n].findAll('div')[4]).split('">', 1)[-1].split('<', 1)[0].strip()
        data[n].append(nilfgaard_score)

        scoia_score = str(soup[n].findAll('div')[7]).split('">', 1)[-1].split('<', 1)[0].strip()
        data[n].append(scoia_score)

        north_score = str(soup[n].findAll('div')[10]).split('">', 1)[-1].split('<', 1)[0].strip()
        data[n].append(north_score)

        skellige_score = str(soup[n].findAll('div')[13]).split('">', 1)[-1].split('<', 1)[0].strip()
        data[n].append(skellige_score)

        monsters_score = str(soup[n].findAll('div')[16]).split('">', 1)[-1].split('<', 1)[0].strip()
        data[n].append(monsters_score)

    embed = discord.Embed(title="Pro Rank Rankings", url=prorank_url, description=prorank_description, color=0xea114d)
    embed.set_author(name="Gwent Masters - Pro", url=prorank_url, icon_url=playgwent_icon_url)
    embed.set_thumbnail(url=masters_logo_url)

    for n in range(5):
        top_label = '{}. {} ~ ***{}***\n'.format(n + 1, data[n][0], data[n][1])
        bottom_label = "MMR: **{}** - Matches: **{}**\nNilfgaard: **{}** - Scoia'tael: **{}** - N. Realms: **{}**\nSkellige: **{}** - Monsters: **{}**".format(
            data[n][3], data[n][2], data[n][4], data[n][5], data[n][6], data[n][7], data[n][8])
        embed.add_field(name=top_label, value=bottom_label, inline=False)

    embed.set_footer(text="Pro Rank - {} at {}".format(time.strftime('%A'), time.strftime('%X')),
                     icon_url=masters_logo_url)

    return embed


def getRankings(tournament):
    copper = 'copper'
    silver = 'silver'
    gold = 'gold'
    rankings_url = ''

    if tournament == 'Open':
        rankings_url = 'https://masters.playgwent.com/en/rankings/crown-open'
        copper = 'copper is-active'

    if tournament == 'Challenger':
        rankings_url = 'https://masters.playgwent.com/en/rankings/crown-challenger'
        silver = 'silver is-active'

    if tournament == 'World Masters':
        rankings_url = 'https://masters.playgwent.com/en/rankings/crown-masters'
        gold = 'gold is-active'

    if tournament == 'Rankings':
        rankings_url = 'https://masters.playgwent.com/en/rankings/crown-masters'
        gold = 'gold is-active'

    soup = parse(rankings_url)

    rankings = soup.find('div', {'class': 'c-ranking-table c-ranking-table--big-crown on-desktop'}).findAll('div', {
        'class': 'c-ranking-table__tr'})

    player_stats = [[] for n in range(11)]
    for num in range(10):
            # country
            country_code = str(rankings[num]).split(
                'flag-icon-', 1)[-1].split('"', 1)[0].upper()
            player_stats[num].append(
                pycountry.countries.get(alpha_2=country_code).name)

            # nickname
            player_stats[num].append(rankings[num].find(
                'div', {'class': 'td-nick'}).find('strong').text)

            # copper = open, silver = challenger, gold = masters score
            player_stats[num].append(rankings[num].find(
                'div', {'class': copper}).find('strong').text)
            player_stats[num].append(rankings[num].find(
                'div', {'class': silver}).find('strong').text)
            player_stats[num].append(rankings[num].find(
                'div', {'class': gold}).find('strong').text)

    description = 'Top players in crown points in Gwent {}'.format(tournament)

    # e.g. players_stats = ['Poland', 'TailBot', '60', '135', '608']...
    embed = discord.Embed(title="Rankings", url=rankings_url,
                          description=description, color=0xea114d)
    embed.set_author(name="Gwent Masters - Crown Points",
                     url=rankings_url, icon_url=playgwent_icon_url)
    embed.set_thumbnail(url=masters_logo_url)

    if tournament == 'Open':
        for num in range(0, 10):
            top_label = '{}. {} ~ ***{}***'.format(
                num + 1, player_stats[num][0], player_stats[num][1])
            bottom_label = 'Open: **{}** - Challenger: {} - World Masters: {}\n'.format(
                player_stats[num][2], player_stats[num][3], player_stats[num][4])
            embed.add_field(name=top_label, value=bottom_label, inline=False)

    if tournament == 'Challenger':
        for num in range(0, 10):
            top_label = '{}. {} ~ ***{}***'.format(
                num + 1, player_stats[num][0], player_stats[num][1])
            bottom_label = 'Open: {} - Challenger: **{}** - World Masters: {}\n'.format(
                player_stats[num][2], player_stats[num][3], player_stats[num][4])
            embed.add_field(name=top_label, value=bottom_label, inline=False)

    if tournament == 'World Masters':
        for num in range(0, 10):
            top_label = '{}. {} ~ ***{}***'.format(
                num + 1, player_stats[num][0], player_stats[num][1])
            bottom_label = 'Open: {} - Challenger: {} - World Masters: **{}**\n'.format(
                player_stats[num][2], player_stats[num][3], player_stats[num][4])
            embed.add_field(name=top_label, value=bottom_label, inline=False)

    if tournament == 'Rankings':
        for num in range(0, 10):
            top_label = '{}. {} ~ ***{}***'.format(
                num + 1, player_stats[num][0], player_stats[num][1])
            bottom_label = 'Open: {} - Challenger: {} - World Masters: {}\n'.format(
                player_stats[num][2], player_stats[num][3], player_stats[num][4])
            embed.add_field(name=top_label, value=bottom_label, inline=False)

    embed.set_footer(text="Crown Points - {} at {}".format(time.strftime('%A'), time.strftime('%X')),
                     icon_url=masters_logo_url)

    return embed

def getPlayGwentProfile(message, array_start):
    profile = message.content[array_start:]
    link_url = 'https://www.playgwent.com/en/profile/' + profile
    soup = parse(link_url)

    # add private player
    avatar_private_url = 'https://i.imgur.com/6wreE6h.png'

    #parsed variables
    # avatar_url gives error in users like 'freddybabes'
    try:
        profile_data_wins = json.loads(str(soup).split('var profileDataWins = ', 1)[-1].split(';', 1)[0])
    except:
        embed = discord.Embed(title=profile,description='This player profile is private.', color=0x12b61f)
        embed.set_author(name="PlayGwent Profile", url=link_url,icon_url=masters_logo_url)
        embed.set_thumbnail(url=avatar_private_url)
        embed.add_field(name='Description:',value='Player {} has set their player profile to private mode. Only {} is able to view it.'.format(profile, profile), inline=True)
        embed.set_footer(text="PlayGwent - Profile - {} at {}".format(time.strftime('%A'), time.strftime('%X')), icon_url=masters_logo_url)

        return embed

    avatar_url = soup.find('div', {'class': 'l-player-details__avatar'}).find('img')['src']
    if avatar_url == 'https://cdn-l-playgwent.cdprojektred.com/avatars/48071.jpg':
        avatar_url = avatar_private_url

    playername = soup.find('strong', {'class': 'l-player-details__name'}).text.strip()
    rank = soup.find('span', {'class': 'l-player-details__rank'}).text
    position = soup.find('div', {'class': 'l-player-details__table-position'}).find('strong').text
    mmr = soup.find('div', {'class': 'l-player-details__table-mmr'}).find('strong').text
    description = soup.find('div', {'class': 'l-player-details__table-ladder'}).find('span').text + ' Player'

    #factions wins data json
    profile_data_wins = json.loads(str(soup).split('var profileDataWins = ', 1)[-1].split(';', 1)[0])
    profile_data_current = json.loads(str(soup).split('var profileDataCurrent = ', 1)[-1].split(';', 1)[0])

    faction = ''
    wins = ''

    #replace len with number of factions in game
    for num in range(len(profile_data_wins['factions'])):
        name = profile_data_wins['factions'][num]['slug'].capitalize()
        if name == 'Northernrealms':
            name = 'Northern Realms'
        if name == 'Scoiatael':
            name = "Scoia'tael"
        faction += name+'\n'

    currentwins = []
    for num in range(0, len(profile_data_wins['factions'])):
        currentwins.append((profile_data_current['factions'][num]['count']))
        currentwins.sort(reverse=True)

    #replace len
    for num in range(len(profile_data_wins['factions'])):
        wins += "`{} won - {} won`\n".format(str(profile_data_wins['factions'][num]['count']), str(currentwins[num]))
    
    statistics_description = 'Position: {} - Rank: {}'.format(position, rank)

    embed = discord.Embed(title=playername, url=link_url,description='{}'.format(description), color=0x12b61f)
    embed.set_author(name="PlayGwent Profile", url=link_url,icon_url=masters_logo_url)
    embed.set_thumbnail(url=avatar_url)
    embed.add_field(name='Statistics:',value=statistics_description, inline=True)
    embed.add_field(name='MMR:', value=mmr, inline=True)
    embed.add_field(name='Faction:', value=faction, inline=True)
    embed.add_field(name='Lifetime W - Current W:', value=wins, inline=True)
    
    try:
        # Current Ranked Season - Stats
        current_ranked_soup = soup.find('table', {'class': 'c-statistics-table current-ranked'}).findAll('tr')
    except:
        embed.set_footer(text="PlayGwent - Profile - {} at {}".format(time.strftime('%A'), time.strftime('%X')), icon_url=masters_logo_url)
        return embed

    matches = int(soup.find('span', {'class': 'profile-matches'}).find('strong').text.split(' matches', 1)[0])
    current_wins = int(current_ranked_soup[2].find('td').next_sibling.text.split(' matches', 1)[0])
    current_loss = int(current_ranked_soup[3].find('td').next_sibling.text.split(' matches', 1)[0])
    current_ties = int(current_ranked_soup[4].find('td').next_sibling.text.split(' matches', 1)[0])
    winrate = round((current_wins / matches) * 100, 2)

    current_count = '{}\n{}\n{}\n{}\n{}%'.format(matches, current_wins, current_loss, current_ties, winrate)

    factions_fmmr = ''
    for num in range(5, 10):
        factions_fmmr += str(current_ranked_soup[num].find('td').text) + '\n'

    fmmr = ''
    for num in range(5, 10):
        fmmr += '`{} fMMR - {} Matches`\n'.format(current_ranked_soup[num].find('td').next_sibling.text.split()[0], current_ranked_soup[num].find('td').next_sibling.text.split()[2],)
    
    current_description = 'Overall\nWins\nLosses\nDraws\nWinrate:'

    embed.add_field(name='Current Ranked Season:',value=current_description, inline=True)
    embed.add_field(name='-', value=current_count, inline=True)
    embed.add_field(name='Faction:', value=factions_fmmr, inline=True)
    embed.add_field(name='-', value=fmmr, inline=True)
    embed.set_footer(text="PlayGwent - Profile - {} at {}".format(time.strftime('%A'), time.strftime('%X')), icon_url=masters_logo_url)

    return embed

def getPlayGwentDeck(message):
    deck_url = getLink(message.content)
    json_file = parsequot(deck_url)

    playgwent_deck = [[] for n in range(0, len(json_file['guide']['deck']['cards']))]

    for num in range(len(playgwent_deck)):
        playgwent_deck[num].append(json_file['guide']['deck']['cards'][num]['localizedName'])
        playgwent_deck[num].append(json_file['guide']['deck']['cards'][num]['rarity'].capitalize())
        playgwent_deck[num].append(json_file['guide']['deck']['cards'][num]['cardGroup'].capitalize())
        playgwent_deck[num].append(int(json_file['guide']['deck']['cards'][num]['repeatCount'])+1)
        playgwent_deck[num].append(int(json_file['guide']['deck']['cards'][num]['power']))
        playgwent_deck[num].append(int(json_file['guide']['deck']['cards'][num]['provisionsCost']))

    #sort in descending order from the provisions cost
    playgwent_deck.sort(key=lambda x: x[5], reverse=True)

    faction_leader = json_file['guide']['deck']['leader']['localizedName']
    deck_name = json_file['guide']['name']
    deck_author = json_file['guide']['author']
    crafting_cost = json_file['guide']['craftingCost']
    provisions_cost = json_file['guide']['deck']['provisionsCost']
    cards_count = json_file['guide']['deck']['cardsCount']

    author_url = 'https://www.playgwent.com/profile/' + deck_author

    deck_image = ''
    deck_faction = json_file['guide']['faction']['slug'].capitalize()

    if deck_faction == 'Monsters':
        deck_image = monsters_cardback
    if deck_faction == 'Nilfgaard':
        deck_image = nilfgaard_cardback
    if deck_faction == 'Skellige':
        deck_image = skellige_cardback
    if deck_faction == 'Northernrealms':
        deck_faction = 'Northern Realms'
        deck_image = northern_cardback
    if deck_faction == 'Scoiatael':
        deck_faction = "Scoia'tael"
        deck_image = scoiatel_cardback

    cards_print = ''
    for num in range(len(playgwent_deck)):
        cards_print += ('{} - `x{} {}`\n'.format(playgwent_deck[num][2][0], playgwent_deck[num][3], playgwent_deck[num][0]))

    embed = discord.Embed(title=deck_name, url=deck_url, description='{} deck by **[{}]({})**'.format(deck_faction, deck_author, author_url), color=0x12b61f)
    embed.set_author(name="Gwent Deck Library", url=deck_url, icon_url=playgwent_icon_url)
    embed.set_thumbnail(url=deck_image)  # add - DEPENDS ON DECK FACTION
    embed.add_field(name="Faction Leader:", value=faction_leader, inline=True)
    embed.add_field(name="Number of Cards:", value=cards_count, inline=True)
    embed.add_field(name="Scraps Cost:", value=crafting_cost, inline=True)
    embed.add_field(name="Provisions Cost:", value=provisions_cost, inline=True)
    embed.add_field(name='Cards:', value=cards_print)
    embed.set_footer(text="PlayGwent - Deck Library - {} at {}".format(time.strftime('%A'), time.strftime('%X')), icon_url=playgwent_icon_url)

    return embed

@client.event
async def on_ready():
    print("Beep Boop, I'm a robot!")
    print('Logged in as:')
    print(client.user.display_name)
    print('------')
    await client.change_presence(game=discord.Game(name="Gwent 2077"))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('!player'):
        embed = getPlayGwentProfile(message, 8)
        await client.send_message(message.channel, embed=embed)
    if message.content.startswith('!profile'):
        embed = getPlayGwentProfile(message, 9)
        await client.send_message(message.channel, embed=embed)
    if message.content.startswith('!prorank'):
        embed = getProRank()
        await client.send_message(message.channel, embed=embed)
    if message.content.startswith('!top10 open'):
        embed = getRankings('Open')
        await client.send_message(message.channel, embed=embed)
    if message.content.startswith('!top10 challenger'):
        embed = getRankings('Challenger')
        await client.send_message(message.channel, embed=embed)
    if message.content.startswith('!top10 worldmasters'):
        embed = getRankings('World Masters')
        await client.send_message(message.channel, embed=embed)
    if message.content.startswith('!rankings'):
        embed = getRankings('Rankings')
        await client.send_message(message.channel, embed=embed)
    if '/decks/guides/' in message.content:
        embed = getPlayGwentDeck(message)
        await client.send_message(message.channel, embed=embed)

client.run(config.token)
