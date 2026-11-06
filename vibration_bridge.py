"""USB waveform + scheduled haptics, with recovery after StickS3 resets."""
import asyncio,time,json,contextlib
import aiohttp,serial
PORT='/dev/cu.usbmodem2101'
async def session():
 port=serial.Serial(port=None,baudrate=115200,timeout=0,write_timeout=.2)
 port.dtr=True;port.rts=False;port.port=PORT;port.open()
 pending=set();sent=0;acks=0;packets=0;fault=None
 port.write(b'\n0\n')
 print('StickS3 serial connected',flush=True)
 def cancel():
  for h in pending:h.cancel()
  pending.clear()
  with contextlib.suppress(serial.SerialException,OSError):port.write(b'0\n')
 def schedule(target):
  nonlocal sent
  delay=target/1000-time.time()
  if delay<-.08:return
  def pulse():
   nonlocal sent,fault
   pending.discard(handle)
   try:port.write(b'B\n');sent+=1
   except (serial.SerialException,OSError) as e:fault=e
  if delay<=0:
   port.write(b'B\n');sent+=1;return
  handle=asyncio.get_running_loop().call_later(delay,pulse);pending.add(handle)
 async def feedback():
  nonlocal acks,fault
  buf=bytearray()
  try:
   while True:
    buf.extend(port.read(min(4096,port.in_waiting)))
    while b'\n' in buf:
     line,_,buf=buf.partition(b'\n')
     if line.startswith(b'ECG '):print(line.decode(errors='replace'),flush=True)
     if b'VIB 80ms' in line:
      acks+=1
      if acks%10==0:print(json.dumps({'sent':sent,'ack':acks,'packets_sent':packets}),flush=True)
    if len(buf)>4096:buf.clear()
    await asyncio.sleep(.02)
  except (serial.SerialException,OSError) as e:fault=e
 task=asyncio.create_task(feedback())
 try:
  async with aiohttp.ClientSession() as client:
   async with client.ws_connect('http://127.0.0.1:8765/ws') as ws:
    while True:
     if fault:raise fault
     d=await ws.receive_json(timeout=3)
     if d.get('type')!='ecg':cancel();continue
     for target in d.get('beat_times_ms',[]):schedule(target)
     await asyncio.sleep(0)
     payload='E,'+str(d.get('bpm') or 0)+','+','.join(str(int(x)) for x in d['samples'])+'\n'
     encoded=payload.encode()
     for offset in range(0,len(encoded),64):
      port.write(encoded[offset:offset+64]);time.sleep(.002)
     packets+=1
 finally:
  cancel();task.cancel()
  with contextlib.suppress(asyncio.CancelledError):await task
  port.close()
async def main():
 while True:
  try:await session()
  except (serial.SerialException,OSError,aiohttp.ClientError,asyncio.TimeoutError,TypeError,ValueError) as e:
   print('Reconnect:',str(e),flush=True);await asyncio.sleep(1)
if __name__=='__main__':asyncio.run(main())
