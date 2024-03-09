#!/usr/bin/env python
"""
@Author: Ryuku
@Date: 05/03/2024
"""
import re 
import time
import json
import httpx
import random
import string
import asyncio
import validators
import argparse
from bs4 import BeautifulSoup   


def banner():
    print("""
        ┳┓     ┓    
        ┣┫┓┏┏┳┓┣┓┏┓╋
        ┛┗┗┻┛┗┗┗┛┗┛┗ V3
            Ryuku wishes you a good viewbotting ^_^
          """)


def extract_vid(livestream):
    """
    This function extracts the video ID from a livestream URL.

    Args:
        livestream (str): The URL of the livestream.
            Example: 'https://rumble.com/v4gdg8c-real-news-and-honest-views.html'

    Returns:
        str: The video ID extracted from the livestream URL, or None if not found.
    """
    if not validators.url(livestream):
        return
    print("(+) Getting the video id...")
    headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
}
    response = httpx.get(livestream, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    script_tags = soup.find_all('script', type='application/ld+json')
    video_id = None
    for script in script_tags:
        json_data = script.string
        if json_data:
            data = json.loads(json_data)
            if isinstance(data, list):
                for item in data:
                    if 'embedUrl' in item:
                        embed_url = item['embedUrl']
                        match = re.search(r'/embed/([^/]+)/', embed_url)
                        video_id = match.group(1)
    return video_id


def generate_user_agent(n):
    """
    Generates user-agents to use when botting.
    Rumble links every viewer_id to the user-agent that was used to generate it, 
    and using a viewer_id with a different user-agent will result in rejection.

    Args:
        n (int): The number of user-agents to generate.

    Returns:
        list: A list of generated user-agents.
    """
    user_agents = []
    for _ in range(n):
        me = "Ryuku-was-here"
        rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user_agents.append(f"{me}{rand}")
    return user_agents

def get_viewer_ids(vid, num):
    """
    This function extracts the viewer IDs.

    Args:
        vid (str): The video id of the livestream, we retrieve this using extract_vid().
        num (int): The number of user-agents to generate.
    Returns:
        tuple: A tuple containing:
            - dict: A dictionary mapping viewer IDs to user-agents.
            - str: The video ID extracted from the livestream URL.
            - str: The channel name.
    """
    print("(+) Getting viewer ids...")
    user_agents = generate_user_agent(num)
    viewer_ids = {}
    url = f"https://rumble.com/embedJS/u3/?request=video&v={vid}"
 
    # since we only get the viewer ids once and re use them
    # i don't want do this as fast as possible, if i see that its too slow i might improve it.
    for user_agent in user_agents:
        headers = {'User-Agent': user_agent}
        try:
            response = httpx.get(url, headers=headers)
            data = response.json()
            viewer_id = data.get('viewer_id')
            video_id = data.get('vid')
            channel = data["author"]["name"]
            if viewer_id:
                viewer_ids[viewer_id] = user_agent
        except Exception as e:
            print(f"something went wrong: {e}")
    return viewer_ids, video_id, channel

async def send_view(url, headers, body, viewer_id, verbose):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=body)
            response.raise_for_status()
            if verbose:
                if response.status_code == 200:
                    print(f"(~) id {viewer_id} was sent and accepted.")
                else:
                    print(f"(~) id {viewer_id} was rejected.")
    except Exception as e:
        print(f"Something went wrong {e}")

async def viewbot(viewer_ids, video_id, verbose):
    url = "https://wn0.rumble.com/service.php?api=7&name=video.watching-now"

    tasks = []
    for viewer_id, user_agent in viewer_ids.items():
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': user_agent
        }
        body = f"video_id={video_id}&viewer_id={viewer_id}"
        tasks.append(send_view(url, headers, body, viewer_id, verbose))

    await asyncio.gather(*tasks)

def main():
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
                    prog='Rumbot',
                    description='rumble video video platform viewbotter, works for livestream only.')
    parser.add_argument("-l", "--link", required=True, action="store", help="livestream link.")
    parser.add_argument("-b", "--bots", required=True, action="store", help="numbers of bots to send.")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, required=False, help="prints if the bots being sent worked or not. (each bot sent)")
    parser.add_argument("-s", "--silent", action="store_true", default=False, required=False, help="if provided it dont print the banner.")
    args = parser.parse_args()

    vid_url = args.link
    bots = int(args.bots)
    verbose = args.verbose

    if not args.silent:
        banner()

    vid_id = extract_vid(vid_url)
    
    if not vid_id:
        print("wrong livestream link bud, try again.")
        return
    viewer_ids, video_id, channel = get_viewer_ids(vid_id, bots)
    
    print(f"(+) Retrieved {bots} bots.")
    print(f"(+) view botting channel: {channel}")
    print("(~) Press Ctrl + C when your done to exit.")
    
    while True:
        try:

            asyncio.run(viewbot(viewer_ids, video_id, verbose))
            # viewbot(viewer_ids, video_id, verbose)
            # we keep sending the same bots every 60 seconds
            time.sleep(60)
        except KeyboardInterrupt as e:
            return

if __name__ == '__main__':
    main()

