# def get_user(username):
#     result = subprocess.run(['node', './tiktok-signature/examples/get_secuid.js', username], capture_output=True, text=True)
#     data = json.loads(result.stdout)
#     return data['userInfo']['user']

import os
import re
import pandas as pd
import subprocess
import json
from datetime import datetime
from collections import Counter
from user_info import get_user_info

def extract_geo_info(text, city_pattern, state_pattern, cities, states):
    city = None
    state = None
    city_match = city_pattern.search(text)
    if city_match:
        res = city_match.group(0).lower()
        proper_city = next((c for c in cities.keys() if c.lower() == res or c.replace(' ','').lower() == res), None)
        if proper_city:
            city = proper_city
            state = cities[proper_city]
    state_match = state_pattern.search(text)
    if state_match:
        res = state_match.group(0).lower()
        proper_state = next((s for s in states.keys() if s.lower() == res), None)
        if proper_state:
            state = states[proper_state]
    return city, state

def get_posts(sec_uid):
    result = subprocess.run(['node', './tiktok-signature/examples/get_posts.js', sec_uid],
                             capture_output=True, text=True)
    data = json.loads(result.stdout)
    return data['itemList']

def extract_video_data(data):
    tag_counter = Counter()
    videos = []
    create_time = 0
    viewtime = []
    for video in data:
        if create_time == 0:
            create_time = datetime.fromtimestamp(video['createTime']).strftime('%Y-%m-%d %H:%M:%S')
        desc = video['desc']
        play_count = video['stats'].get('playCount', 0)
        videos.append((video, play_count))
        viewtime.append(play_count)
        for part in desc.split():
            if part.startswith('#') and not part.lower().startswith(('#foryou', '#fy')):
                tag_counter[part[1:]] += 1
    videos = sorted(videos, key=lambda x: x[1], reverse=True)
    video_desc = [v[0]['desc'] for v in videos]
    tags = str(tag_counter)
    return {
        'video_desc': video_desc,
        'most_recent_upload': create_time,
        'tags': tags,
        'viewcounts': viewtime,
    }

def process_user(row, index):
    username = row.get('username')
    if not username:
        return index, None, "Error: Missing Username"
    try:
        user = get_user_info(username)
        sec_uid = user.get('secUid')
        if not sec_uid:
            return index, None, "Error: Missing secUid"
        user_data = {
            'bio': user.get('signature', ''),
            'profile_pic': user.get('profile_pic', ''),
            'video_count': user.get('videos', 0),
            'verified': user.get('verified', False),
            'comment_setting': user.get('commentSetting', ''),
            'region': user.get('region', '')
        }
    except Exception:
        return index, None, "Error Getting UserInfo"
    try:
        posts = get_posts(sec_uid)
        result = extract_video_data(posts)
        video_data = {
            'video_desc': ';'.join(result.get('video_desc', [])),
            'most_recent_upload': result.get('most_recent_upload', ''),
            'viewcounts': ';'.join(map(str, result.get('viewcounts', []))),
            'hashtags': result.get('tags', ''),
        }
        return index, {**video_data, **user_data}, None
    except Exception as e:
        return index, None, f"Error occurred: {e}"

def scrape(dir, start_index=0, end_index=None):
    # Setup geo dictionaries and regex patterns
    cities = {
        'New York': 'NY', 'Los Angeles': 'CA', 'Chicago': 'IL', 'Houston': 'TX',
        'Phoenix': 'AZ', 'Philadelphia': 'PA', 'San Antonio': 'TX', 'San Diego': 'CA',
        'Dallas': 'TX', 'San Jose': 'CA', 'Austin': 'TX', 'Jacksonville': 'FL',
        'Miami': 'FL', 'Tampa': 'FL', 'Columbus': 'OH', 'San Francisco': 'CA',
        'Indianapolis': 'IN', 'Seattle': 'WA', 'Denver': 'CO', 'Washington': 'DC',
        'Boston': 'MA', 'Atlanta': 'GA', 'Pittsburgh': 'PA', 'Cleveland': 'OH',
        'Portland': 'OR', 'Nashville': 'TN', 'New Orleans': 'LA', 'Minneapolis': 'MN',
        'Milwaukee': 'WI', 'Las Vegas': 'NV', 'Salt Lake City': 'UT', 'Santa Fe': 'NM',
        'Cincinnati': 'OH', 'Detroit': 'MI', 'Santa Monica': 'CA', 'Fort Worth': 'TX',
        'Sacramento': 'CA', 'Santa Barbara': 'CA', 'Albuquerque': 'NM', 'Oklahoma City': 'OK',
        'Kansas City': 'MO', 'Charlotte': 'NC', 'Virginia Beach': 'VA', 'Baltimore': 'MD',
        'Jersey City': 'NJ', 'Newark': 'NJ'
    }
    # Add tight format keys
    cities.update({city.replace(' ', '').lower(): state for city, state in cities.items() if ' ' in city})
    states = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
        'District of Columbia': 'DC', 'Cali': 'CA'
    }
    states.update({state.replace(' ', '').lower(): abb for state, abb in states.items() if ' ' in state})
    city_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(c) for c in cities.keys()) + r')\b', re.IGNORECASE)
    state_pattern = re.compile(r'\b(?:' + '|'.join(re.escape(s) for s in states.keys()) + r')\b', re.IGNORECASE)

    for filename in os.listdir(dir):
        if not filename.endswith('.csv'):
            continue
        file_path = os.path.join(dir, filename)
        df = pd.read_csv(file_path, low_memory=False)
        df_slice = df.iloc[start_index:end_index] if end_index else df.iloc[start_index:]
        for index, row in df_slice.iterrows():
            try:
                index, result, error = process_user(row, index)
                if error:
                    print(f"Index {index}: {error}")
                    continue
                # Update expected fields
                fields = ['video_desc', 'most_recent_upload', 'viewcounts', 'hashtags',
                          'bio', 'profile_pic', 'video_count', 'verified', 'comment_setting', 'region']
                for key in fields:
                    df.at[index, key] = result.get(key, '')

                # Dynamically extract city/state from combined text
                combined_text = " ".join([
                    result.get('bio', ''),
                    result.get('video_desc', ''),
                    result.get('hashtags', '')
                ])

                creator_city, creator_state = extract_geo_info(combined_text, city_pattern, state_pattern, cities, states)
                if creator_city:
                    df.at[index, "inferred_city"] = creator_city
                if creator_state:
                    df.at[index, "inferred_state"] = creator_state
                if index % 10 == 0:
                    df.to_csv(file_path, index=False)
                    print(f"Finished processing {index} influencers in {filename}")

            except Exception as e:
                print(f"Failed to process index {index} in {filename}: {e}")
        df.to_csv(file_path, index=False)
        print(f"Completed processing {filename}")

if __name__ == "__main__":
    import sys
    directory = sys.argv[1]
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end_index = int(sys.argv[3]) if len(sys.argv) > 3 else None
    scrape(directory, start_index=start_index, end_index=end_index)