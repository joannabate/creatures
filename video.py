import cv2
import numpy as np
import pandas as pd
from data import load_data, get_start_index
import multiprocessing as mp
from time import sleep, time
from random import randint, choice
from datetime import datetime
import os

class Video:
    def __init__(self, df, width=1360, height=768, window_name='clock'):
        self.df = df
        self.width = width
        self.height = height
        self.background_color = (0,0,0)
        self.window_name = window_name
        self.font_color = (0,0,255)
        self.max_fps = 40

        self.videos = self.get_videos()

        # Assume default sunset and sunrise times
        self.sunrise = 360
        self.sunset = 1080
        
        # Subtract a quarter because it takes a moment to load the video
        self.music_changes = [x - 1 for x in [720, 1104, 1232, 1360, 48, 176]]

        self.season_end_dates = [
            {'season': 'autumn', 'date': pd.Timestamp('2022-12-21').date(), 'date_name': 'winter solstice'},
            {'season': 'winter', 'date': pd.Timestamp('2023-03-20').date(), 'date_name': 'spring equinox '},
            {'season': 'spring', 'date': pd.Timestamp('2023-06-21').date(), 'date_name': 'summer solstice'},
            {'season': 'summer', 'date': pd.Timestamp('2023-09-22').date(), 'date_name': 'autumn equinox'},
            {'season': 'autumn', 'date': pd.Timestamp('2023-12-21').date(), 'date_name': 'winter solstice'}
        ]

    # Returns a dict of folders : filenames
    def get_videos(self, path='videos'):
        videos = {}
        for root, dirs, files in os.walk(path):
            # If the directory has files in it
            if len(dirs) == 0:
                # Keep only video files
                files = [ file for file in files if file.endswith( ('.mp4','.mov') ) ]
                videos[root] = files
        return videos
        
    def change_brightness(self, img, value=30):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v,value)
        v[v > 255] = 255
        v[v < 0] = 0
        final_hsv = cv2.merge((h, s, v))
        img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        return img

    def create_blank(self):
        # Create black blank image
        image = np.zeros((self.height, self.width, 3), np.uint8)

        # Since OpenCV uses BGR, convert the colors before using
        rgb_color = tuple(reversed(self.background_color))

        # Fill image with color
        image[:] = rgb_color

        return image

    def get_season(self, i):
        current_date = self.df.loc[i, "Timestamp"].date()

        for season in self.season_end_dates:
            if current_date < season['date']:
                bottom_text = "%d days until %s" % ((season['date'] - current_date).days, season['date_name'])
                break
            elif current_date == season['date']:
                bottom_text = season['date_name'].upper()
                break

        return season['season'], bottom_text

    def get_day_segment(self, i):
            
            day_idx = i % 1440

            # If it's daytime
            if self.df.iloc[i]['Direct Beam']  > 0.5:
                # Calc divisions between time of day
                segment_length = int((self.sunset - self.sunrise)/4)
                midday_start = self.sunrise + segment_length
                midday_end = self.sunset - segment_length
                # print(str(day_idx))
                # print('midday start: ' + str(midday_start))
                # print('midday end: ' + str(midday_end))
                if day_idx > midday_start and day_idx < midday_end:
                    day_segment = 'midday'
                elif day_idx < 720:
                    day_segment = 'sunrise'
                else:
                    day_segment = 'sunset'
            else:
                day_segment = 'night'

            # print(day_segment)
            return day_segment

    def run(self, i, bpm, step_on_flag):

        i_last = -1
        day_segment_last = None
        day_segment = self.get_day_segment(i.value)
        season, bottom_text = self.get_season(i.value)
        frame_time_last = time()
        start_time = time()
        step_time_last = time()
        video = None

        ft = cv2.freetype.createFreeType2()
        ft.loadFontData(fontFileName='Fondamento-Regular.ttf', id=0)

        while True:
            print('loading video')

            if day_segment == 'night':
                video = choice([x for x in self.videos['videos/night'] if x != video])
                cap = cv2.VideoCapture('videos/night/' + video)
            elif day_segment == 'midday':
                video = choice([x for x in self.videos['videos/midday/' + season] if x != video])
                cap = cv2.VideoCapture('videos/midday/' + season + '/' + video)
            else:
                video = choice([x for x in self.videos['videos/' + day_segment] if x != video])
                cap = cv2.VideoCapture('videos/' + day_segment + '/' + video)

            fps = int(cap.get(cv2.CAP_PROP_FPS))

            adjusted_fps = fps * bpm.value/100

            n = 0
            skip_frames = 1

            while cap.isOpened():

                # ret, frame = cap.read()
                ret = cap.grab()

                if ret == True:

                    # If step is on and it's been more than three seconds since we last broke, break and start over
                    if step_on_flag.value:
                        if (time() - step_time_last) > 3:
                            step_time_last = time()
                            break

                    n = n + 1
                    if n % skip_frames == 0:
                        
                        _, frame = cap.retrieve() #decode frame

                        frame_time = time()
                        actual_fps = 1/(frame_time - frame_time_last)
                        frame_time_last = frame_time

                        # print('adjusted fps: ' + str(adjusted_fps))
                        # print('actual fps: ' + str(actual_fps))
                        # print('skip frames: ' + str(skip_frames))

                        sleep((1/adjusted_fps) - ((time() - start_time) % (1/adjusted_fps)))

                        if i.value != i_last: # timestep has changed
                            # print("i = ", i.value)
                            i_last = i.value

                            adjusted_fps = fps * bpm.value/100
                            skip_frames = int(adjusted_fps/self.max_fps) + 1
                            adjusted_fps = adjusted_fps/skip_frames

                            # Get index for hour of day
                            day_idx = i.value % 1440

                            # Set season and bottom text
                            season, bottom_text = self.get_season(i.value)

                            # If day segment has changed, break and start over
                            if self.get_day_segment(i.value) != day_segment:
                                day_segment_last = day_segment
                                day_segment = self.get_day_segment(i.value)

                                print('Day segment has changed from ' + day_segment_last + ' to ' + day_segment)
                                # Update sunrise and sunset times
                                if day_segment == 'sunrise' and day_segment_last == 'night':
                                    self.sunrise = day_idx
                                elif day_segment == 'night' and day_segment_last == 'sunset':
                                    self.sunset = day_idx
                                break

                            # If music has changed break and start over
                            if day_idx in self.music_changes:
                                print('Music has changed')
                                break

                            row = self.df.iloc[i.value]

                            if row['Timestamp'].hour < 10:
                                padding = 25
                            else:
                                padding = 0

                            time_text=row['Timestamp'].strftime("%-I:%M")
                            am_pm_text =row['Timestamp'].strftime("%p").lower()

                            # If it's night
                            if day_segment == 'night':
                                # Inverse of below
                                brightness_reduction = row['Direct Beam'] * 2 * 255
                            else:
                                # No reduction when brightness is 1 (i.e. midday)
                                # full reduction when brightness is 0.5 (i.e. sunset/sunrise)
                                brightness_reduction = (1 - (row['Direct Beam'] - 0.5) * 2) * 255
                                

                        # Resize frame
                        frame = cv2.resize(frame, (self.width, self.height))

                        #Adjust brightness
                        frame = self.change_brightness(frame, value=-brightness_reduction)

                        # Add in time
                        ft.putText(img=frame,
                            text=time_text,
                            org=(225+padding, 250),
                            fontHeight=150,
                            color=(255,  255, 255),
                            thickness=-1,
                            line_type=cv2.LINE_AA,
                            bottomLeftOrigin=True)
                        
                        # Add in am/pm
                        ft.putText(img=frame,
                            text=am_pm_text,
                            org=(325, 375),
                            fontHeight=100,
                            color=(255,  255, 255),
                            thickness=-1,
                            line_type=cv2.LINE_AA,
                            bottomLeftOrigin=True)
                        
                        # Add in bottom text
                        ft.putText(img=frame,
                            text=bottom_text,
                            org=(50, 550),
                            fontHeight=50,
                            color=(255,  255, 255),
                            thickness=-1,
                            line_type=cv2.LINE_AA,
                            bottomLeftOrigin=True)
                            

                        cv2.imshow(self.window_name, frame)
                        cv2.namedWindow(self.window_name, cv2.WINDOW_FULLSCREEN)
                        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) #Disable when on large monitor
                        # cv2.resizeWindow(self.window_name, self.width, self.height) #Enable when on large monitor

                        k = cv2.waitKey(1)
                        if k==27:    # Esc key to stop
                            cap.release()
                            cv2.destroyAllWindows()
                            return
                else:
                    print('returning to start of video')
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)


if __name__ == "__main__":
    df = load_data(cached=True)
    i = mp.Value('i', 0)
    j = mp.Value('i', 0)
    element = mp.Value('i', 0)

    my_video = Video(df)
    # my_video.run(i, j)
