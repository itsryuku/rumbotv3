#!/usr/bin/env python
"""
@Author: Ryuku
@Date: 05/03/2024
"""
import re 
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

async def generate_user_agent(n):
    """
    Generates user-agents to use when botting.
    Rumble links every viewer_id to the user-agent that was used to generate it, 
    and using a viewer_id with a different user-agent will result in rejection.

    Args:
        n (int): The number of user-agents to generate.

    Returns:
        list: A list of generated user-agents.
    """
    camouflage = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.54 Mobile Safari/537.36"
    user_agents = []
    for _ in range(n):
        rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user_agents.append(camouflage+rand)
    return user_agents

async def get_viewer_ids(vid, num):
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
    print("(+) Getting viewer ids, Please wait...")
    viewer_ids = {}
    url = f"https://rumble.com/embedJS/u3/?request=video&v={vid}"

    async with httpx.AsyncClient() as client:
        for i in range(num):
            user_agent = await generate_user_agent(1) # if it works, it works.
            headers = {'User-Agent': user_agent[0]}
            response = await client.get(url, headers=headers)
            try:
                data = response.json()
                viewer_id = data.get('viewer_id')
                video_id = data.get('vid')
                channel = data["author"]["name"]
                if viewer_id:
                    viewer_ids[viewer_id] = user_agent[0]
                print(f"\r(+) Retrieved {i+1}/{num}", end='', flush=True)
            except Exception as e:
                print(f"something went wrong: {e}")

    print()
    return viewer_ids, video_id, channel

async def viewbot(viewer_ids, video_id, verbose):
    url = "https://wn0.rumble.com/service.php?api=7&name=video.watching-now"

    async with httpx.AsyncClient() as client:
        tasks = []
        for viewer_id, user_agent in viewer_ids.items():
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': user_agent
            }
            body = f"video_id={video_id}&viewer_id={viewer_id}"
            task = asyncio.create_task(send_view(client, url, headers, body, viewer_id, verbose))
            tasks.append(task)
        
        await asyncio.gather(*tasks)

async def send_view(client, url, headers, body, viewer_id, verbose):
    try:
        response = await client.post(url, headers=headers, data=body)
        response.raise_for_status()
        if verbose:
            if response.status_code == 200:
                print(f"(~) id {viewer_id} was sent and accepted.")
            else:
                print(f"(~) id {viewer_id} was rejected.")
    except Exception as e:
        print(f'ops: {e}')


async def main():
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
    viewer_ids, video_id, channel = await get_viewer_ids(vid_id, bots)
    
    print(f"(+) view botting channel: {channel}")
    print("(~) Press Ctrl + C when your done to exit.")
    
    while True:
        try:
            await viewbot(viewer_ids, video_id, verbose)
            await asyncio.sleep(60)
        except KeyboardInterrupt as e:
            return

if __name__ == '__main__':
    asyncio.run(main())


