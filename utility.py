import sys
import os
import pandas as pd
import csv
# directory, change this!
dir = './demodata'

def filter_processed_data(dir):
    for filename in os.listdir(dir):
        if filename.endswith('csv'):
            file_path = os.path.join(dir, filename)
            df = pd.read_csv(file_path, low_memory=False)
            filtered_df = df[df['hashtags'].notna()]
            filtered_df.to_csv(os.path.join(dir, 'filtered.csv'), index=False)

# filter_processed_data(dir)

import ast
from collections import Counter

def make_junction_table(dir):
    for filename in os.listdir(dir):
        if filename.endswith('csv'):
            file_path = os.path.join(dir, filename)
            df = pd.read_csv(file_path, low_memory=False)
            
            # Step 1: Parse hashtags and create unique hashtags list
            hashtag_to_id = {}
            hashtag_id_counter = 1
            influencer_hashtag_counts = []

            # Iterate through influencer data to populate hashtags
            for index, row in df.iterrows():
                influencer_id = row['id']
                try:
                    hashtag_counter = ast.literal_eval(row['hashtags'])
                except ValueError:
                    # If literal_eval fails, try evaluating as a Counter string
                    hashtag_counter = eval(row['hashtags'])

                for hashtag, count in hashtag_counter.items():
                    if hashtag not in hashtag_to_id:
                        hashtag_to_id[hashtag] = hashtag_id_counter
                        hashtag_id_counter += 1
                    # Record (influencer_id, hashtag_id, count)
                    influencer_hashtag_counts.append(
                        [influencer_id, hashtag_to_id[hashtag], count]
                    )

            # Step 2: Write hashtag.csv with unique hashtags
            with open(dir+'/hashtag.csv', mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["id", "name"])
                for hashtag, id_ in hashtag_to_id.items():
                    writer.writerow([id_, hashtag])
    
            # Step 3: Write hashtag-influencers.csv with influencer hashtag usage
            with open(dir+'hashtag-influencers.csv', mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["influencer_id", "hashtag_id", "count"])
                writer.writerows(influencer_hashtag_counts)

make_junction_table(dir)