#include "wireless.h"
#include <M5Unified.h>
constexpr int MOTOR=0, COUNT=1000;
int16_t samples[COUNT];int head=0,used=0,bpm=0;unsigned long until=0,lastData=0,lastDraw=0;unsigned packets=0;
char line[1400];int lineLen=0;bool overflow=false;
M5Canvas canvas(&M5.Display);
void command(){
 line[lineLen]=0;
 if(!strcmp(line,"B")){digitalWrite(MOTOR,HIGH);until=millis()+80;Serial.println("VIB 80ms");}
 else if(!strcmp(line,"0")){digitalWrite(MOTOR,LOW);until=0;}
 else if(line[0]=='E' && line[1]==','){
  char* save;char* token=strtok_r(line+2,",",&save);if(!token)return;
  int rate=atoi(token);int16_t incoming[100];int n=0;
  while((token=strtok_r(nullptr,",",&save)) && n<100)incoming[n++]=atoi(token);
  if(n!=100)return;
  bpm=rate;for(int i=0;i<n;i++){samples[head]=incoming[i];head=(head+1)%COUNT;if(used<COUNT)used++;}
  lastData=millis();packets++;if(packets%25==0)Serial.printf("ECG %u\n",packets);
 }
}
void draw(){
 canvas.fillSprite(0x0841);canvas.setTextSize(1);canvas.setTextColor(TFT_WHITE);
 canvas.setCursor(5,4);canvas.printf("LIVE ECG  %s",millis()-lastData<2500 && used?"WiFi":"WAIT");
 canvas.setCursor(170,4);if(bpm && millis()-lastData<2500)canvas.printf("%d BPM",bpm);else canvas.print("-- BPM");
 for(int x=0;x<240;x+=20)canvas.drawFastVLine(x,22,90,0x18e3);
 for(int y=22;y<113;y+=18)canvas.drawFastHLine(0,y,240,0x18e3);
 if(used>1){
  int lo=32767,hi=-32768;for(int i=0;i<used;i++){int v=samples[(head-used+i+COUNT)%COUNT];lo=min(lo,v);hi=max(hi,v);}
  float mid=(lo+hi)*.5f,range=max(100,hi-lo);int px=0,py=67;
  for(int x=0;x<240;x++){int i=x*(used-1)/239;int v=samples[(head-used+i+COUNT)%COUNT];int y=constrain((int)(67-(v-mid)*80/range),23,111);if(x)canvas.drawLine(px,py,x,y,0x87f0);px=x;py=y;}
 }
 canvas.setCursor(5,122);canvas.printf("4s | ADC | %u packets",packets);canvas.pushSprite(0,0);
}
void setup(){
 wifiBegin();
 pinMode(MOTOR,OUTPUT);digitalWrite(MOTOR,LOW);auto cfg=M5.config();cfg.internal_spk=false;cfg.internal_mic=false;M5.begin(cfg);
 Serial.begin(115200);M5.Display.setRotation(1);M5.Display.setBrightness(100);canvas.setColorDepth(16);canvas.createSprite(240,135);draw();
}
void loop(){
 M5.update();
 if(wifiRead(line,sizeof(line))){lineLen=strlen(line);command();lineLen=0;}
 if(until && (long)(millis()-until)>=0){digitalWrite(MOTOR,LOW);until=0;}
 if(millis()-lastDraw>=80 && !until){draw();lastDraw=millis();}
 delay(1);
}
