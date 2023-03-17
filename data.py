import pandas as pd
from datetime import datetime
import numpy as np
import pickle
from pytz import timezone
import random

def load_data(cached=False):
    if cached:
        return pickle.load(open( "data.pickle", "rb") )
    else:
        df = pd.read_csv('irradiance.csv')

        # Expand from hourly to minute
        df_mins = pd.DataFrame(data={'mins': range(0, 60)})

        df['key'] = 0
        df_mins['key'] = 0

        df = df.merge(df_mins, on='key', how='outer')

        df['Timestamp'] = pd.to_datetime(df['Timestamp']) + pd.to_timedelta(df['mins'], unit='m')

        df.drop(columns=['key', 'mins'], inplace=True)

        # Apply a rolling window and average. Data is reversed to get a forward looking average.
        df.loc[:, df.columns!='Timestamp'] = df.loc[:, df.columns!='Timestamp'][::-1].rolling(60, min_periods=1).mean()[::-1]

        # Normalize entire dataset between 1.25 and 0, then clip to 1
        df.loc[:, df.columns!='Timestamp'] = df.loc[:, df.columns!='Timestamp'].apply(lambda x: 1.25 * (x - x.min())/(x.max() - x.min())).clip(upper=1)

        #Add new column with brightness, created from sine waves randomly varying in frequency
        s = pd.Series(dtype='float')

        while len(s) < len(df):
            s = pd.concat([s, np.sin(pd.Series(range(0, 360, random.randint(1, 5))) * np.pi / 180)])

        df = df.merge(s.rename('Brightness', inplace=True).reset_index(), how='left', left_index=True, right_index=True)

        pickle.dump(df, open( "data.pickle", "wb"))

        return df


def get_start_index(df):

    start_time = datetime.now()
    decimal_time = int(start_time.hour)/24 + int(start_time.minute)/(24*60) + int(start_time.second)/(24*60*60)

    first_date = datetime(year=2022, month=12, day=21)
    data_duration = (365*24*60*60)

    data_start_time = first_date.timestamp() + (decimal_time * data_duration)

    data_start_time = datetime.fromtimestamp(data_start_time, timezone('Etc/GMT+8'))

    # Filter to correct point in data based on time of day
    return df[df['Timestamp'] > np.datetime64(data_start_time)].head(1).index[0]

if __name__ == '__main__':
    df = load_data(cached=False)
    print(df)