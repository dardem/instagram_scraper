import pandas as pd
import os
import glob
from settings.general import TAGS


def glue_by_tags(data_path='data/', tags=[]):
    df = pd.DataFrame(
        columns=['text', 'hashtags', 'datetime', 'likes', 'owner',
                 'owner_followers',
                 'owner_number_posts'])

    if len(tags) > 0:
        for tag in tags:
            if not os.path.isdir(data_path + tag):
                continue

            for fname in glob.glob(data_path + tag + '/*.csv'):
                df = df.append(pd.read_csv(fname).drop('Unnamed: 0', axis=1))

    else:
        subdirs = [x[0] for x in os.walk(data_path)]
        for subdir in subdirs[1:]:
            for fname in glob.glob(subdir + '/*.csv'):
                df = df.append(pd.read_csv(fname).drop('Unnamed: 0', axis=1))

    df.to_csv('data/all_posts.csv')


glue_by_tags('backups/all_posts/', TAGS)
