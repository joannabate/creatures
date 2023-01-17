import os
import glob
from scipy.io import wavfile
import sounddevice as sd

class Audio:
    def __init__(self):
        self.samples = []
        
        self.samples.append({'folder': 'Synth Loops',
                        'subfolder': 'Drop Loops',
                        'key': True,
                        'bpm': True})

        self.samples.append({'folder': 'Synth Loops',
                        'subfolder': 'Breakdown Loops',
                        'key': True,
                        'bpm': True})

        for i, meta in enumerate(self.samples):
            path = 'samples/' + meta['folder'] + '/' + meta['subfolder']
            files = os.listdir(path)

            sample_list = []

            for filename in glob.glob(os.path.join(path, '*.wav')):
                samplerate, data = wavfile.read(filename)

                samplename = filename.split('.')[0]
                samplename_parts = []
                samplename_parts = samplename.split(' ')
                key = samplename_parts[-2] + samplename_parts[-1]
                bpm = samplename_parts[-4]

                if meta['key'] and meta['bpm']:
                
                    sample_list.append({'name': samplename,
                        'rate': samplerate,
                        'key': key,
                        'bpm': bpm,
                        'data': data})

            self.samples[i]['samples'] = sample_list

if __name__ == '__main__':
    audio = Audio()
    for meta in audio.samples:
        for sample in meta['samples']:
            sd.play(sample['data'], blocking=True)



