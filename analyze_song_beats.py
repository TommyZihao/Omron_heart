import numpy as np,json
from pathlib import Path
x=np.fromfile('/tmp/heartbeat-song.raw',dtype=np.float32);sr=11025;hop=128;n=512
frames=np.lib.stride_tricks.sliding_window_view(x,n)[::hop]
spec=np.abs(np.fft.rfft(frames*np.hanning(n),axis=1));flux=np.maximum(np.diff(np.log1p(spec),axis=0),0).sum(axis=1)
t=(np.arange(len(flux))+1)*hop/sr+n/2/sr
# Estimate phase and period against onset strength over the main body.
mask=(t>20)&(t<180);tt=t[mask];ff=flux[mask];best=None
for bpm in np.arange(125,131,.02):
 period=60/bpm
 for phase in np.arange(0,period,.004):
  distance=np.abs((tt-phase+period/2)%period-period/2)
  score=np.sum(ff*np.exp(-.5*(distance/.022)**2))
  if best is None or score>best[0]:best=(score,bpm,phase)
_,bpm,phase=best;period=60/bpm
beats=[]
for target in np.arange(phase,t[-1],period):
 indices=np.where(abs(t-target)<.065)[0]
 if len(indices):
  weights=flux[indices]*np.exp(-.5*((t[indices]-target)/.03)**2)
  beats.append(round(float(t[indices[np.argmax(weights)]]),4))
Path('heartbeat/song-beats.json').write_text(json.dumps({'bpm':round(bpm,3),'phase':phase,'beats':beats}))
print('BPM',bpm,'phase',phase,'beats',len(beats))
