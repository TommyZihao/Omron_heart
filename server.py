import asyncio, json, struct, time, statistics
import serial,os
from collections import deque
from pathlib import Path
from aiohttp import web
from bleak import BleakClient, BleakScanner
NOTIFY='5052fff7-4f4e-5f45-4347-5f3030303030'
WRITE='5052fff8-4f4e-5f45-4347-5f3030303030'
state={'status':'扫描设备','packets':0,'beats':0,'bpm':None,'last_data':0,'sample_rate':250,'source':'live','mode':'low_latency'}
clients=set()
led=None
pending_led=set()
def cancel_leds():
 for handle in pending_led: handle.cancel()
 pending_led.clear()
 if led and led.is_open:
  try: led.write(b'0')
  except serial.SerialException: pass
async def serial_feedback():
 buffer=bytearray()
 while True:
  try:
   if led.in_waiting:
    buffer.extend(led.read(min(4096,led.in_waiting)))
    while b'\n' in buffer:
     line,_,rest=buffer.partition(b'\n');buffer=bytearray(rest)
     if b'PULSE GPIO4+GPIO2 80ms' in line:state['led_ack']=state.get('led_ack',0)+1
   await asyncio.sleep(.02)
  except serial.SerialException as e:
   state['led_status']=str(e);return
def schedule_led(delay):
 def pulse():
  pending_led.discard(handle)
  if time.time()-state['last_data']<1:
   try:
    led.write(b'B')
    if not isinstance(led,WirelessOnly):state['led_sent']=state.get('led_sent',0)+1
   except serial.SerialException as e:state['led_status']=str(e)
 handle=asyncio.get_running_loop().call_later(delay,pulse)
 pending_led.add(handle)

class Detector:
 def __init__(self):
  self.base=None;self.lp=0.;self.prev=0.;self.energy=deque(maxlen=10);self.history=deque(maxlen=500);self.n=0;self.last=-1000;self.rr=deque(maxlen=6);self.armed=True
 def feed(self,x):
  self.n+=1
  if self.base is None:self.base=x
  self.base+=.012*(x-self.base);self.lp+=.4*(x-self.base-self.lp)
  delta=self.lp-self.prev;self.prev=self.lp;self.energy.append(delta*delta);e=sum(self.energy)/len(self.energy);self.history.append(e)
  if len(self.history)<500:return False
  threshold=max(4., sorted(self.history)[int(len(self.history)*.90)]*.5)
  if e<threshold*.45:self.armed=True
  if self.armed and e>threshold and self.n-self.last>75:
   rr=(self.n-self.last)/250
   if .3<rr<2:self.rr.append(rr)
   self.last=self.n;self.armed=False;return True
  return False
async def broadcast(data):
 for ws in list(clients):
  try:await ws.send_json(data)
  except Exception:clients.discard(ws)
async def bluetooth():
 while True:
  detector=Detector();last_seq=None
  try:
   state['status']='扫描设备';device=await BleakScanner.find_device_by_name('ECG-D01M01',timeout=20)
   if not device:raise RuntimeError('未扫描到 ECG-D01M01')
   state['status']='连接设备'
   async with BleakClient(device,timeout=15) as client:
    queue=asyncio.Queue();buffer=bytearray()
    def receive(_,data):queue.put_nowait(bytes(data))
    await client.start_notify(NOTIFY,receive)
    # Confirmed in OMRON Plus: command 0x04 requests real-time ECG transmission.
    await client.write_gatt_char(WRITE,bytes.fromhex('aa040007000b0d'),response=False)
    state['status']='已连接，等待心电数据';print(state,flush=True)
    while client.is_connected:
     try:data=await asyncio.wait_for(queue.get(),timeout=8)
     except asyncio.TimeoutError:raise RuntimeError('8秒未收到数据；手机可能占用连接')
     buffer.extend(data)
     while len(buffer)>=6:
      if buffer[0]!=0xaa:del buffer[0];continue
      length=int.from_bytes(buffer[2:4],'big')
      if length<6 or length>4096:del buffer[0];continue
      if len(buffer)<length:break
      frame=bytes(buffer[:length]);del buffer[:length]
      if frame[-1]!=13 or sum(frame[1:-2])&255!=frame[-2]:continue
      if frame[1]!=27 or len(frame)!=210:continue
      samples=list(struct.unpack('<100h',frame[8:208]));seq=int.from_bytes(frame[4:8],'little')
      if last_seq is not None and seq != ((last_seq+1)&0xffffffff):
       detector=Detector();cancel_leds();state['gaps']=state.get('gaps',0)+1
      last_seq=seq
      beats=[]
      for i,x in enumerate(samples):
       if detector.feed(x):beats.append(i);state['beats']+=1
      state.update(status='实时接收',packets=state['packets']+1,last_data=time.time(),bpm=round(60/statistics.median(detector.rr)) if detector.rr else None)
      playback_at_ms=time.time()*1000+(50 if state['mode']=='smooth' else 0)
      beat_times_ms=[playback_at_ms+(i*4 if state['mode']=='smooth' else 0) for i in beats]
      for target in beat_times_ms:schedule_led(max(0,(target-time.time()*1000)/1000))
      await broadcast(dict(type='ecg',samples=samples,beat_indices=beats,playback_at_ms=playback_at_ms,beat_times_ms=beat_times_ms,sequence=seq,**state))
      if state['packets']%25==0:print(json.dumps(state,ensure_ascii=False),flush=True)
  except Exception as e:
   cancel_leds()
   state['status']=str(e);state['bpm']=None;print('BLE:',e,flush=True);await broadcast(dict(type='status',**state));await asyncio.sleep(3)
async def ws_handler(request):
 ws=web.WebSocketResponse();await ws.prepare(request);clients.add(ws);await ws.send_json(dict(type='status',**state))
 try:
  async for msg in ws:
   if msg.type!=web.WSMsgType.TEXT:continue
   try:command=json.loads(msg.data)
   except (ValueError,TypeError):continue
   if isinstance(command,dict) and command.get('type')=='set_mode' and command.get('mode') in ('smooth','low_latency'):
    cancel_leds();state['mode']=command['mode']
    await broadcast(dict(type='mode',**state))
 finally:clients.discard(ws)
 return ws
class WirelessOnly:
 is_open=True
 in_waiting=0
 def write(self,data):return len(data)
 def reset_input_buffer(self):pass
 def open(self):pass
 def close(self):self.is_open=False
async def device_status(request):
 try:
  data=json.loads((Path(__file__).parent/'wireless/status.json').read_text())
  if time.time()-data.get('updated',0)>3:data={'device_states':{}}
 except (OSError,ValueError):data={'device_states':{}}
 return web.json_response(data)
async def main():
 global led
 led=WirelessOnly() if os.getenv('HEARTBEAT_WIRELESS')=='1' else serial.Serial(port=None,baudrate=115200,timeout=0,write_timeout=.5)
 led.dtr=False;led.rts=False;led.port='/dev/cu.usbserial-0001';led.open()
 await asyncio.sleep(2);led.reset_input_buffer();led.write(b'0')
 state.update(led_status='WiFi 桥接' if isinstance(led,WirelessOnly) else 'GPIO2 + GPIO4 已连接',led_sent=0,led_ack=0)
 feedback=asyncio.create_task(serial_feedback())
 app=web.Application();app.router.add_static('/icons/',Path(__file__).parent/'web/icons');app.router.add_get('/devices',device_status);app.router.add_get('/music.m4a',lambda r:web.FileResponse(Path(__file__).parent/'web/media/zui-xuan-min-zu-feng.m4a'));app.router.add_get('/',lambda r:web.FileResponse(Path(__file__).parent/'web/index.html'));app.router.add_get('/ws',ws_handler);app.router.add_get('/status',lambda r:web.json_response(state))
 runner=web.AppRunner(app);await runner.setup();await web.TCPSite(runner,'127.0.0.1',8765).start();print('http://127.0.0.1:8765',flush=True);
 try:await bluetooth()
 finally:
  cancel_leds();feedback.cancel();led.close();await runner.cleanup()
if __name__=='__main__':asyncio.run(main())
