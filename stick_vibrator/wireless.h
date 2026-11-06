#include <WiFi.h>
#include <WiFiUdp.h>
WiFiUDP udp;
const char* TOKEN="omron-heart-demo-change-me";
const char* DEVICE="stick";
uint32_t lastHello=0,lastSeq=0;bool gotSeq=false;
void wifiBegin(){WiFi.mode(WIFI_STA);WiFi.setSleep(false);WiFi.setAutoReconnect(true);WiFi.begin("OmronHeartDemo","change-this-password");udp.begin(8767);}
bool wifiRead(char* out,size_t capacity){
 if(WiFi.status()!=WL_CONNECTED)return false;
 if(millis()-lastHello>=200){lastHello=millis();IPAddress ip=WiFi.localIP(),mask=WiFi.subnetMask();IPAddress broadcast((uint32_t)ip|~(uint32_t)mask);udp.beginPacket(broadcast,8766);udp.printf("%s|HELLO|%s|%lu",TOKEN,DEVICE,(unsigned long)millis());udp.endPacket();}
 int size=udp.parsePacket();if(!size)return false;
 char buf[1500];int n=udp.read(buf,sizeof(buf)-1);if(n<=0)return false;buf[n]=0;
 char* save;char* tok=strtok_r(buf,"|",&save);if(!tok||strcmp(tok,TOKEN))return false;
 tok=strtok_r(nullptr,"|",&save);if(!tok)return false;uint32_t stamp=strtoul(tok,nullptr,10);if(millis()-stamp>800)return false;
 tok=strtok_r(nullptr,"|",&save);if(!tok)return false;uint32_t seq=strtoul(tok,nullptr,10);if(gotSeq&&(int32_t)(seq-lastSeq)<=0)return false;
 tok=strtok_r(nullptr,"|",&save);if(!tok||strlen(tok)>=capacity)return false;strcpy(out,tok);lastSeq=seq;gotSeq=true;
 udp.beginPacket(udp.remoteIP(),8766);udp.printf("%s|ACK|%s|%lu|%c",TOKEN,DEVICE,(unsigned long)seq,out[0]);udp.endPacket();return true;
}
