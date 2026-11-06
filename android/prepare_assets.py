"""Copy the current local web UI into the offline Android app; preserve pairing seed."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parent
web=root.parent/'web'
s=(web/'index.html').read_text()
a=s.index('function connect(){');b=s.index('setInterval(',a)
start=s.index('const d=JSON.parse(e.data);',a);end=s.index(';ws.onclose=',start)
body=s[start:end]
assert body.endswith('}')
body=body[len('const d=JSON.parse(e.data);'):-1]
body="$('nativeStatus').textContent=d.status||'';"+body
s=s[:a]+'window.nativeEvent=function(d){'+body+'};\n'+s[b:]
s=s.replace('</header>','</header><section class="native-controls"><button onclick="HeartbeatAndroid.start()">开始连接</button><button onclick="HeartbeatAndroid.stop()">停止</button><button onclick="HeartbeatAndroid.hotspot()">热点</button><small id="nativeStatus">点击开始连接</small></section>',1)
s=s.replace('ECG-D01M01 → Mac 蓝牙 → 心搏检测 → 虚拟灯','ECG-D01M01 → 手机蓝牙 → 心搏检测 → 热点 → ESP32 / StickS3')
s=s.replace('src="/music.m4a" preload="metadata"','preload="metadata"')
s=s.replace("music.volume=.4;", """$('musicToggle').disabled=true;$('musicRestart').disabled=true;
fetch('/music.m4a').then(r=>{if(!r.ok)throw Error('音频资源读取失败');return r.blob();}).then(blob=>{musicUrl=URL.createObjectURL(blob);music.src=musicUrl;music.load();$('musicToggle').disabled=false;$('musicRestart').disabled=false;}).catch(e=>{$('musicError').hidden=false;$('musicError').textContent=e.message;});
setInterval(()=>HeartbeatAndroid.audioStatus(JSON.stringify({paused:music.paused,time:music.currentTime,ready:music.readyState,error:music.error?.code,context:audioContext?.state,enabled:musicEnabled})),5000);
music.volume=.4;""")
(root/'assets/index.html').write_text(s)
shutil.copyfile(web/'media/zui-xuan-min-zu-feng.m4a',root/'assets/music.m4a')
shutil.copyfile(root.parent/'wireless/token',root/'assets/token')
if not (root/'assets/sequence').exists():
 (root/'assets/sequence').write_text(str(int((root.parent/'wireless/sequence_reservation').read_text())+1000000))

shutil.copytree(web/'icons',root/'assets/icons',dirs_exist_ok=True)
