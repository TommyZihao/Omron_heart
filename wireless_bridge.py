import asyncio,time,json,os
from pathlib import Path
import aiohttp
TOKEN=(Path(__file__).parent/'wireless/token').read_text().strip()
# Reserve sequence ranges so restart cannot look like delayed packets to devices.
SEQ_FILE=Path(__file__).parent/'wireless/sequence_reservation'
seq=int(SEQ_FILE.read_text()) if SEQ_FILE.exists() else int(time.time())+86400
seq &= 0xffffffff
reserved=1000000
SEQ_FILE.write_text(str((seq+reserved)&0xffffffff))
peers={};acks={};transport=None;pending=set()
class UDP(asyncio.DatagramProtocol):
 def datagram_received(self,data,addr):
  try:
   t,kind,name,*rest=data.decode().split('|')
   if t!=TOKEN or name not in ('led','stick'):return
   if kind=='HELLO':
    stamp=int(rest[0]);peers[name]=(addr,stamp,time.monotonic())
   elif kind=='ACK' and name in peers and peers[name][0]==addr:
    acks[name]=acks.get(name,0)+1
  except (ValueError,UnicodeError,IndexError):pass
 def error_received(self,exc):print('UDP',exc,flush=True)
def send(payload,only=None):
 global seq,reserved
 if reserved<=1:
  SEQ_FILE.write_text(str((seq+1000000)&0xffffffff));reserved=1000000
 seq=(seq+1)&0xffffffff;reserved-=1
 for name,(addr,stamp,seen) in list(peers.items()):
  if time.monotonic()-seen>.6 or (only and name!=only):continue
  transport.sendto(f'{TOKEN}|{stamp}|{seq}|{payload}'.encode(),addr)
def cancel():
 for h in pending:h.cancel()
 pending.clear();send('0')
async def report():
 while True:
  status={'updated':time.time(),'device_states':{name:{'online':name in peers and time.monotonic()-peers[name][2]<1,'acks':acks.get(name,0)} for name in ('led','stick')}}
  temporary=Path(__file__).parent/'wireless/status.tmp'
  temporary.write_text(json.dumps(status));temporary.replace(temporary.with_name('status.json'))
  await asyncio.sleep(.5)
async def main():
 global transport
 transport,_=await asyncio.get_running_loop().create_datagram_endpoint(UDP,local_addr=('0.0.0.0',8766),allow_broadcast=True)
 reporter=asyncio.create_task(report())
 try:
  async with aiohttp.ClientSession() as client:
   while True:
    try:
     async with client.ws_connect('http://127.0.0.1:8765/ws') as ws:
      while True:
       d=await ws.receive_json(timeout=3)
       if d.get('type')!='ecg':cancel();continue
       for target in d.get('beat_times_ms',[]):
        delay=target/1000-time.time()
        if delay<-.08:continue
        if delay<=0:send('B')
        else:
         def fire(box):pending.discard(box[0]);send('B')
         box=[];h=asyncio.get_running_loop().call_later(delay,fire,box);box.append(h);pending.add(h)
       send('E,'+str(d.get('bpm') or 0)+','+','.join(map(str,d['samples'])),'stick')
    except (aiohttp.ClientError,asyncio.TimeoutError,TypeError):cancel();await asyncio.sleep(1)
 finally:cancel();reporter.cancel();transport.close()
if __name__=='__main__':asyncio.run(main())
