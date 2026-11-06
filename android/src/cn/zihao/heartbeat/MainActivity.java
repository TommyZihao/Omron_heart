package cn.zihao.heartbeat;
import android.app.*;import android.os.*;import android.content.*;import android.content.pm.PackageManager;import android.webkit.*;import android.net.Uri;import java.io.*;import java.util.*;
public class MainActivity extends Activity {
 WebView web;boolean ready=false; final Handler main=new Handler(Looper.getMainLooper());
 final HeartbeatService.Listener listener=data->main.post(()->{if(ready&&web!=null)web.evaluateJavascript("window.nativeEvent("+data+")",null);});
 @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(128);web=new WebView(this);setContentView(web);web.setOnApplyWindowInsetsListener((v,insets)->{android.graphics.Insets bars=insets.getInsets(android.view.WindowInsets.Type.systemBars());v.setPadding(bars.left,bars.top,bars.right,bars.bottom);return insets;});
  web.setBackgroundColor(0xff100b10);web.getSettings().setJavaScriptEnabled(true);web.getSettings().setDomStorageEnabled(true);web.getSettings().setAllowFileAccess(false);web.getSettings().setAllowContentAccess(false);web.getSettings().setMediaPlaybackRequiresUserGesture(true);
  web.addJavascriptInterface(new Bridge(),"HeartbeatAndroid");
  web.setWebChromeClient(new WebChromeClient(){@Override public boolean onConsoleMessage(ConsoleMessage m){android.util.Log.i("HeartbeatAudio",m.message());return true;}});
  web.setWebViewClient(new WebViewClient(){
   @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return !"heartbeat.local".equals(r.getUrl().getHost());}
   @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){
    if(!"heartbeat.local".equals(r.getUrl().getHost()))return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));
    String path=r.getUrl().getPath();String file="/music.m4a".equals(path)?"music.m4a":path!=null&&path.matches("/icons/[a-z0-9_-]+\\.png")?path.substring(1):"index.html";
    try{return new WebResourceResponse(file.endsWith("m4a")?"audio/mp4":file.endsWith("png")?"image/png":"text/html","UTF-8",getAssets().open(file));}catch(IOException e){return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream("资源读取失败".getBytes()));}
   }
   @Override public void onPageFinished(WebView v,String u){ready=true;listener.onData(HeartbeatService.snapshot());}
  });web.loadUrl("https://heartbeat.local/index.html");
  if(getIntent().hasExtra("record_seconds")&&checkSelfPermission("android.permission.BLUETOOTH_CONNECT")==0&&checkSelfPermission("android.permission.BLUETOOTH_SCAN")==0)startForegroundService(new Intent(this,HeartbeatService.class).putExtra("record_seconds",getIntent().getIntExtra("record_seconds",180)));
 }
 @Override public void onStart(){super.onStart();HeartbeatService.listener=listener;listener.onData(HeartbeatService.snapshot());}
 @Override public void onDestroy(){if(HeartbeatService.listener==listener)HeartbeatService.listener=null;ready=false;web.destroy();web=null;super.onDestroy();}
 void start(){ArrayList<String> p=new ArrayList<>();for(String s:new String[]{"android.permission.BLUETOOTH_SCAN","android.permission.BLUETOOTH_CONNECT","android.permission.POST_NOTIFICATIONS"})if(checkSelfPermission(s)!=PackageManager.PERMISSION_GRANTED)p.add(s);if(!p.isEmpty()){requestPermissions(p.toArray(new String[0]),7);return;}startForegroundService(new Intent(this,HeartbeatService.class));}
 @Override public void onRequestPermissionsResult(int r,String[] p,int[] g){super.onRequestPermissionsResult(r,p,g);if(r==7){if(checkSelfPermission("android.permission.BLUETOOTH_SCAN")==0&&checkSelfPermission("android.permission.BLUETOOTH_CONNECT")==0)startForegroundService(new Intent(this,HeartbeatService.class));else web.evaluateJavascript("document.getElementById('nativeStatus').textContent='需要附近设备权限才能连接心电贴'",null);}}
 class Bridge {
  @JavascriptInterface public void audioStatus(String value){android.util.Log.i("HeartbeatAudio",value);}
  @JavascriptInterface public void start(){main.post(()->MainActivity.this.start());}
  @JavascriptInterface public void stop(){main.post(()->stopService(new Intent(MainActivity.this,HeartbeatService.class)));}
  @JavascriptInterface public void hotspot(){main.post(()->{try{startActivity(new Intent("android.settings.TETHER_SETTINGS"));}catch(Exception e){startActivity(new Intent(android.provider.Settings.ACTION_WIRELESS_SETTINGS));}});}
 }
}
